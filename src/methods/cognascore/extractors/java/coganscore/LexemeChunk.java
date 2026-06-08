package coganscore;

public record LexemeChunk(String lexeme, int line, LexemeType type) {
    public LexemeChunk {
        if (type == null) {
            type = LexemeType.NORMAL;
        }
    }
}
