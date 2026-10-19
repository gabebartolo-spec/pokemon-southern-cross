require "minitest/autorun"

class TestHarness < Minitest::Test
  def test_loader_finds_test_files
    files = Dir[File.join(__dir__, "test_*.rb")]
    assert_includes files.map { |f| File.basename(f) }, "test_harness.rb"
  end
end
