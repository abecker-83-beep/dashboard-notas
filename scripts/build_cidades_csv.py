import io
import os
import re
import zipfile
import tempfile
import requests
import pandas as pd
import geopandas as gpd
import unicodedata


IBGE_ZIP_URL = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/Brasil/BR_Municipios_2024.zip"


def normalizar_texto(valor: str) -> str:
    valor = str(valor).strip().upper()
    valor = unicodedata.normalize("NFKD", valor).encode("ASCII", "ignore").decode("ASCII")
    valor = re.sub(r"\s+", " ", valor)
    return valor


def encontrar_coluna(candidatas, colunas):
    colunas_upper = {c.upper(): c for c in colunas}
    for cand in candidatas:
        if cand.upper() in colunas_upper:
            return colunas_upper[cand.upper()]
    raise ValueError(f"Nenhuma das colunas {candidatas} encontrada em {list(colunas)}")


def main():
    os.makedirs("data", exist_ok=True)

    print("Baixando malha municipal do IBGE...")
    resp = requests.get(IBGE_ZIP_URL, timeout=120)
    resp.raise_for_status()

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "BR_Municipios_2024.zip")
        with open(zip_path, "wb") as f:
            f.write(resp.content)

        print("Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        shp_path = None
        for root, _, files in os.walk(tmpdir):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_path = os.path.join(root, file)
                    break
            if shp_path:
                break

        if not shp_path:
            raise FileNotFoundError("Nenhum arquivo .shp encontrado dentro do ZIP do IBGE.")

        print(f"Lendo shapefile: {shp_path}")
        gdf = gpd.read_file(shp_path)

        col_municipio = encontrar_coluna(
            ["NM_MUN", "nome", "NOME", "municipio", "MUNICIPIO"],
            gdf.columns
        )
        col_uf = encontrar_coluna(
            ["SIGLA_UF", "UF", "uf"],
            gdf.columns
        )
        col_ibge = encontrar_coluna(
            ["CD_MUN", "CD_MUN_7", "geocodigo", "id"],
            gdf.columns
        )

        print("Calculando ponto representativo de cada município...")
        pontos = gdf.geometry.representative_point()

        saida = pd.DataFrame({
            "Cidade": gdf[col_municipio].astype(str).apply(normalizar_texto),
            "UF": gdf[col_uf].astype(str).apply(normalizar_texto),
            "lat": pontos.y.round(6),
            "lon": pontos.x.round(6),
            "ibge_id": gdf[col_ibge].astype(str),
        })

        saida = saida.drop_duplicates(subset=["Cidade", "UF"]).sort_values(["UF", "Cidade"])

        out_path = os.path.join("data", "cidades.csv")
        saida.to_csv(out_path, index=False, encoding="utf-8")
        print(f"Arquivo gerado com sucesso: {out_path}")
        print(f"Total de linhas: {len(saida)}")


if __name__ == "__main__":
    main()
