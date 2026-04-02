class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/cli-v4.0.0-alpha/merger-cli-macos.tar.gz"
  sha256 "f41ea9c5972de8b4d6fe885dd52cf36dd9aee4d134c7d7cdf151fe03c5ec4da5"
  license "GPLv3"

  depends_on "libmagic"

  def install
    libexec.install Dir["merger-cli-macos/*"]
    bin.install_symlink libexec/"merger"
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
