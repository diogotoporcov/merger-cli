class MergerCli < Formula
  desc "Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
  homepage "https://github.com/diogotoporcov/merger-cli"
  url "https://github.com/diogotoporcov/merger-cli/releases/download/{{VERSION}}/merger-cli-macos.tar.gz"
  sha256 "{{SHA256}}"

  depends_on "libmagic"

  def install
    bin.install "merger-cli-macos" => "merger"
  end

  test do
    system "#{bin}/merger", "--version"
  end
end
