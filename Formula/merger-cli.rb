class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/cli-v4.0.0-alpha.7/merger-cli-macos.tar.gz"
  sha256 "eb3df12a266f1a2bc8f55c7b77c68717f233852c5c3f9d7b1cffed5a23c3d97b"
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
