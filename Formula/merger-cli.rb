class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/cli-v4.0.0-alpha.1/merger-cli-macos.tar.gz"
  sha256 "c6f49f3e2878b7b84156ec241a1d503eec9f34e2d388bdd82503952abf475b57"
  license "GPLv3"

  depends_on "libmagic"

  def install
    bin.install "merger-cli-macos" => "merger"
  end

  test do
    # Basic check to ensure the binary is functional
    assert_match "merger", shell_output("#{bin}/merger --version")
    # Test merge logic with a simple test directory
    (testpath/"test.txt").write("Hello, World!")
    shell_output("#{bin}/merger . -o merged.txt")
    assert_predicate testpath/"merged.txt", :exist?
  end
end
