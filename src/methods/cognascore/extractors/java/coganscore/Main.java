package coganscore;

import coganscore.util.JavaSourceParser;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class Main {
    public static void main(String[] args) throws Exception {
        Path sourcePath = args.length == 0
                ? Path.of("examples", "example.java")
                : Path.of(args[0]);

        String source = Files.readString(sourcePath);
        JavaSourceParser.ParseResult parsed = JavaSourceParser.parseSource(source, sourcePath.toUri());

        List<LexemeChunk> chunks = new ArrayList<>();
        chunks.addAll(new AstLexemeExtractor(parsed.trees()).extract(parsed.ast()));
        chunks.addAll(new CommentLexemeExtractor().extract(source));
        chunks.sort(Comparator.comparingInt(LexemeChunk::line).thenComparing(LexemeChunk::lexeme));

        System.out.println("line,type,lexeme");
        for (LexemeChunk chunk : chunks) {
            System.out.printf("%d,%s,%s%n", chunk.line(), chunk.type(), csv(chunk.lexeme()));
        }
    }

    private static String csv(String value) {
        if (value == null) {
            return "";
        }
        boolean quote = value.contains(",") || value.contains("\"") || value.contains("\n");
        String escaped = value.replace("\"", "\"\"");
        return quote ? "\"" + escaped + "\"" : escaped;
    }
}
