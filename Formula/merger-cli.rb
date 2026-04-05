class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/cli-v4.0.0-alpha.11/merger-cli-macos.tar.gz"
  sha256 "522cc31128bddfe8d33ce134f2310dc927b1c871c037ef6a8f4c2ea8c3049228"
  license "GPL-3.0-or-later"

  depends_on "libmagic"

  def install
    libexec.install Dir["merger-cli-macos/*"]
    bin.install_symlink libexec/"merger"
  end

  test do
    assert_match "merger", shell_output("#{bin}/merger --version")
  end
end
