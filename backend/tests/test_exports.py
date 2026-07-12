"""Phase 2: Export module tests."""
from app.services.export.markdown import storyboard_to_markdown, storyboard_to_script


class TestMarkdownExport:
    def test_storyboard_to_markdown(self, mock_project):
        result = storyboard_to_markdown(mock_project)
        assert result.startswith("# Test Project")
        assert "## Act 1" in result
        assert "Shot" in result
        assert "Father" in result
        assert "BGM" in result

    def test_empty_storyboard(self, mock_project):
        mock_project.storyboard = {"projectName": "", "globalBGM": "", "scenes": []}
        result = storyboard_to_markdown(mock_project)
        assert "#" in result

    def test_storyboard_no_scenes(self):
        class MockP:
            storyboard = {"projectName": "Empty", "globalBGM": "", "scenes": []}
        result = storyboard_to_markdown(MockP())
        assert "Empty" in result


class TestScriptExport:
    def test_storyboard_to_script(self, mock_project):
        result = storyboard_to_script(mock_project)
        assert "Shot" in result or "Project:" in result
        assert "[" in result  # Should contain shot type markers

    def test_empty_script(self):
        class MockP:
            storyboard = {"projectName": "Empty", "globalBGM": "", "scenes": []}
        result = storyboard_to_script(MockP())
        assert "Empty" in result


class TestPDFExport:
    def test_storyboard_to_pdf(self, mock_project):
        from app.services.export.pdf import storyboard_to_pdf
        result = storyboard_to_pdf(mock_project)
        assert result.startswith(b"%PDF")

    def test_empty_pdf(self):
        class MockP:
            storyboard = {"projectName": "Empty", "globalBGM": "", "scenes": []}
        from app.services.export.pdf import storyboard_to_pdf
        result = storyboard_to_pdf(MockP())
        assert result.startswith(b"%PDF")
