from tad.services.writer import FileSystemWriter, S3Writer, GitWriter


def test_file_system_writer_empty_yaml():
    data = None
    location = "./"
    file_system_writer = FileSystemWriter(data, location)
    file_system_writer.write()

    # os check if location exists
    # is content gelijk aan wat we verwachten
    pass


def test_file_system_writer_yaml_with_content():
    data = {"test": "test"}
    location = "./"
    FileSystemWriter(data, location)

    # os check if location exists
    # is content gelijk aan wat we verwachten
    pass


def test_git_writer():
    pass


def test_s3_writer():
    pass
