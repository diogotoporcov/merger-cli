class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/cli-v4.0.0-alpha.5/merger-cli-macos.tar.gz"
  sha256 "3b38fafc78264d7a68c78133b32d21d5b5430cc3218ca1d6c1d01f1fc0de453d"
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
