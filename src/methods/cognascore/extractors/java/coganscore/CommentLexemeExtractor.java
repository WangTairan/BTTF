package coganscore;

import java.util.ArrayList;
import java.util.List;

public class CommentLexemeExtractor {
    public List<LexemeChunk> extract(String code) {
        List<LexemeChunk> result = new ArrayList<>();
        if (code == null || code.isEmpty()) {
            return result;
        }

        int n = code.length();
        char[] src = code.toCharArray();
        int i = 0;
        int line = 1;

        while (i < n) {
            if (i + 1 < n && src[i] == '/' && src[i + 1] == '/') {
                int start = i + 2;
                int j = start;
                while (j < n && src[j] != '\n') {
                    j++;
                }

                String lexeme = normalize(code.substring(start, j));
                if (!lexeme.isEmpty()) {
                    result.add(new LexemeChunk("comment_" + lexeme, line, LexemeType.COMMENT));
                }

                i = j;
                continue;
            }

            if (i + 1 < n && src[i] == '/' && src[i + 1] == '*') {
                int blockStart = i + 2;
                int j = blockStart;
                while (j + 1 < n && !(src[j] == '*' && src[j + 1] == '/')) {
                    j++;
                }

                int blockEnd = j;
                if (j + 1 < n) {
                    j += 2;
                }

                String rawBlock = code.substring(blockStart, blockEnd);
                int currentLine = line;
                for (String commentLine : splitAndCleanBlockComment(rawBlock)) {
                    String lexeme = normalize(commentLine);
                    if (!lexeme.isEmpty()) {
                        result.add(new LexemeChunk("comment_" + lexeme, currentLine, LexemeType.COMMENT));
                    }
                    currentLine++;
                }

                line += rawBlock.split("\n", -1).length - 1;
                i = j;
                continue;
            }

            if (src[i] == '\n') {
                line++;
            }
            i++;
        }

        return result;
    }

    private static List<String> splitAndCleanBlockComment(String raw) {
        List<String> out = new ArrayList<>();
        if (raw == null) {
            return out;
        }

        boolean first = true;
        for (String line : raw.split("\n")) {
            if (first) {
                first = false;
                line = line.replaceFirst("^\\s*/?\\*+", "");
            }
            line = line.replaceFirst("^\\s*\\*+", "").trim();
            if (!line.isEmpty()) {
                out.add(line);
            }
        }
        return out;
    }

    private static String normalize(String value) {
        if (value == null) {
            return "";
        }
        return value.trim().replaceAll("\\s+", "_");
    }
}
