"""Tests for Google Drive folder resolution and duplicate handling."""

from unittest.mock import MagicMock, patch

from praisonaippt.gdrive_uploader import GDriveUploader


def _uploader_with_mock_service(list_side_effect):
    uploader = GDriveUploader.__new__(GDriveUploader)
    service = MagicMock()
    service.files.return_value.list.return_value.execute.side_effect = list_side_effect
    uploader.service = service
    return uploader, service


def test_get_folder_id_by_name_uses_oldest_folder():
    responses = [
        {
            "files": [
                {"id": "older", "name": "06", "createdTime": "2026-06-01T08:09:12.000Z"},
                {"id": "newer", "name": "06", "createdTime": "2026-06-01T08:09:12.200Z"},
            ]
        }
    ]
    uploader, service = _uploader_with_mock_service(responses)

    folder_id = uploader.get_folder_id_by_name("06", parent_id="year-folder")

    assert folder_id == "older"
    call_kwargs = service.files.return_value.list.call_args.kwargs
    assert call_kwargs["orderBy"] == "createdTime"


def test_get_or_create_folder_reuses_existing_without_create():
    responses = [{"files": [{"id": "existing", "name": "06", "createdTime": "2026-06-01T08:09:12.000Z"}]}]
    uploader, service = _uploader_with_mock_service(responses)

    folder_id, created = uploader.get_or_create_folder("06", parent_id="year-folder")

    assert folder_id == "existing"
    assert created is False
    service.files.return_value.create.assert_not_called()


@patch("praisonaippt.gdrive_uploader.time.sleep")
def test_get_or_create_folder_picks_oldest_after_parallel_create(mock_sleep):
    responses = [
        {"files": []},
        {
            "files": [
                {"id": "first", "name": "06", "createdTime": "2026-06-01T08:09:12.165Z"},
                {"id": "second", "name": "06", "createdTime": "2026-06-01T08:09:12.178Z"},
            ]
        },
    ]
    uploader, service = _uploader_with_mock_service(responses)
    service.files.return_value.create.return_value.execute.return_value = {"id": "second"}

    folder_id, created = uploader.get_or_create_folder("06", parent_id="year-folder")

    assert folder_id == "first"
    assert created is True
    service.files.return_value.create.assert_called_once()
    mock_sleep.assert_called()


def test_find_file_by_name_uses_most_recently_modified():
    responses = [
        {
            "files": [
                {"id": "newer-file", "name": "deck.pptx", "modifiedTime": "2026-06-01T09:00:00.000Z"},
                {"id": "older-file", "name": "deck.pptx", "modifiedTime": "2026-06-01T08:00:00.000Z"},
            ]
        }
    ]
    uploader, service = _uploader_with_mock_service(responses)

    file_id = uploader.find_file_by_name("deck.pptx", folder_id="month-folder")

    assert file_id == "newer-file"
    call_kwargs = service.files.return_value.list.call_args.kwargs
    assert call_kwargs["orderBy"] == "modifiedTime desc"


def test_escape_query_value():
    uploader = GDriveUploader.__new__(GDriveUploader)
    assert uploader._escape_query_value("Abraham's deck") == "Abraham\\'s deck"
