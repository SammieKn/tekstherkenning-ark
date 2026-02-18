from tekstherkenning_ark.constants import CACHE_DIR

if __name__ == "__main__":
    llm_cache_files = [f for f in CACHE_DIR.glob("*.pkl") if not "_docai_result" in f.name]
    for cache_file in llm_cache_files:
        print(f"Deleting cache file: {cache_file}")
        cache_file.unlink()
