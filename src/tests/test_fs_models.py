import pytest

from helper import qtmodel


@pytest.fixture
def fs_model() -> qtmodel.FileExplorerModel:
    return qtmodel.FileExplorerModel(None)


def test_add_files_0(fs_model: qtmodel.FileExplorerModel):
    indexes = fs_model.addFiles([
        "s/t.py",
        "s/a/d.py",
        "s/a/e.py",
        "s/x/d.py",
        "s/x/et/x.py",
        "s/x/et/_.py",
        "s/x/j/a.py",
        "s/x/j/c.py",
    ])

    assert fs_model.rowCount() == 1
    folder_s = indexes[0].parent()
    assert fs_model.rowCount(folder_s) == 3
    folder_a = indexes[2].parent()
    assert fs_model.rowCount(folder_a) == 2
    folder_x = indexes[4].parent().parent()
    assert fs_model.rowCount(folder_x) == 3


def test_add_files_1(fs_model: qtmodel.FileExplorerModel):
    indexes = fs_model.addFiles([
        "/a/b/1.c",
        "/a/b/2.c",
        "/a/c/1.c",
    ])

    assert fs_model.rowCount() == 1
    folder_b = indexes[0].parent()
    assert fs_model.rowCount(folder_b) == 2
    folder_c = indexes[2].parent()
    assert fs_model.rowCount(folder_c) == 1
    folder_a = indexes[2].parent().parent()
    assert fs_model.rowCount(folder_a) == 2


def test_add_files_2(fs_model: qtmodel.FileExplorerModel):
    indexes = fs_model.addFiles([
        "/a/b/1.c",
        "/a/b/2.c",
        "/a/b/c/1.c",
        "/a/b/c/2.c",
    ])

    assert fs_model.rowCount() == 1
    folder_b = indexes[0].parent()
    assert fs_model.rowCount(folder_b) == 3
    folder_c = indexes[2].parent()
    assert fs_model.rowCount(folder_c) == 2
    folder_a = indexes[0].parent().parent()
    assert fs_model.rowCount(folder_a) == 1
