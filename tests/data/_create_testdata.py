"""
Helper to create test data for the tests.
Two steps:
- create or copy the data from the CONSTANTS
- in conftest.py the fixtures will load data from tests/data

This module handles first step (only).

Step 1: Create or copy the relevant cache data.
Provide a test PDF and output path cache in create_testdata.ini, then run this script to create the test data.

create_testdata.ini - which you must create yourself, with the following content:

[DEFAULT]
test_pdf_path =  C:\repos\tekstherkenning-ark\data\.cache\KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325.pdf
output_path_cache = C:\repos\tekstherkenning-ark\tests\data\

The function create_testdata() reads the ini file, extracts the paths, runs the classification and parsing functions on the test PDF,
 and creates the test data in subfolder of output_path_cache with stem name pdf.
 Recommended to use subfolder in tests/data/ for output_path_cache, when intention is to create unit tests for this repo.
"""
import os
import pickle
import configparser
from pathlib import Path
from importlib import reload

from tekstherkenning_ark.smart_document import SmartDocument
from tekstherkenning_ark.models.rak import Rak
from tekstherkenning_ark import constants

TESTDATA_INI_PATH = __file__.replace("_create_testdata.py", "create_testdata.ini")


def create_testdata():
    """
    Create testdata (pickle with pdf_path and relevant sections) for init SmartDoc
    """
    # read ini file
    config = configparser.ConfigParser()
    config.read(TESTDATA_INI_PATH)
    pdf_path = config["DEFAULT"]["test_pdf_path"]
    output_patch_cache = config["DEFAULT"]["output_path_cache"]

    # create smart document
    doc = SmartDocument.from_pdf(Path(pdf_path), use_cache=True)
    # save only pdf_path and relevant sections to prevent VERY bloated tests/data
    relevant_sections = []
    for idx, sectie in enumerate(doc.sections):
        if "meettabel" in sectie.titel.lower() and sectie.tabellen:
            relevant_sections.append(idx)
        if "Constructie" in sectie.titel:
            relevant_sections.extend([idx, idx + 1, idx + 2, idx+3])  # include next 3 sections as well
    # unique and sort and select
    relevant_sections = sorted(set(relevant_sections))
    relevant_sections = [doc.sections[i] for i in relevant_sections]


    output_cache_file = Path(output_patch_cache) / f"{Path(pdf_path).stem}_docai_result.pkl"
    output_cache_file.parent.mkdir(parents=True, exist_ok=True)
    # write bytes
    output_cache_file.write_bytes(pickle.dumps({"pdf_path": doc.pdf_path, "sections": relevant_sections}))

    # load doc from cache to verify it works and to create the rak instance
    doc_from_cache = pickle.loads(output_cache_file.read_bytes())
    loaded_doc = SmartDocument(pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"], analyze_result=None)

    # AND rak instance -save only relevant Rak sections to save some size.
    constants.CACHE_DIR = output_patch_cache
    _ = Rak.from_smart_document(loaded_doc)  # sets LLM cache in output_patch_cache as well


def get_testdata():
    """for debugging purposes/writing tests"""
    # set cache dir to tests/data/KZG0202 dir
    constants.CACHE_DIR = __file__.replace("_create_testdata.py", "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325")
    cached_doc_path = constants.CACHE_DIR / "KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_docai_result.pkl"
    # load data
    doc_from_cache = pickle.loads(cached_doc_path.read_bytes())
    loaded_doc = SmartDocument(pdf_path=doc_from_cache["pdf_path"], sections=doc_from_cache["sections"],
                               analyze_result=None)
    # return rak
    kzg0202_from_test_cache = Rak.from_smart_document(loaded_doc)
    return kzg0202_from_test_cache


if __name__ == "__main__":
    create_testdata()
    # kzg0202_from_test_cache = get_testdata()