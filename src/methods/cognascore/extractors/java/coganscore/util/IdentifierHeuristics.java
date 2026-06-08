package coganscore.util;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

public class IdentifierHeuristics {
    private static final Set<String> IDENT_BLACKLIST = Set.of(
            "aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff", "gggg", "hhhh",
            "llll", "mmmm", "nnnn", "oooo", "pppp", "qqqq", "rrrr", "tttt", "wwww"
    );

    private static final Pattern UNDERSCORE_EDGE = Pattern.compile("^_+|_+$");
    private static final Pattern UNDERSCORE_FOLD = Pattern.compile("_+");
    private static final Pattern SUBTOKEN_BOUNDARY = Pattern.compile(
            "(?<=[a-z])(?=[A-Z])"
                    + "|(?<=[A-Z])(?=[A-Z][a-z])"
                    + "|(?<=[A-Za-z])(?=\\d)"
                    + "|(?<=\\d)(?=[A-Za-z])"
    );

    public static boolean isLikelyJunk(String identifier) {
        List<String> subtokens = subtokenize(identifier);
        return subtokens.size() == 1 && IDENT_BLACKLIST.contains(subtokens.get(0));
    }

    public static List<String> subtokenize(String identifier) {
        if (identifier == null || identifier.isEmpty()) {
            return List.of();
        }

        String normalized = UNDERSCORE_EDGE.matcher(identifier).replaceAll("");
        normalized = UNDERSCORE_FOLD.matcher(normalized).replaceAll("_");

        List<String> tokens = new ArrayList<>();
        for (String part : normalized.split("_")) {
            if (part.isEmpty()) {
                continue;
            }
            for (String token : SUBTOKEN_BOUNDARY.split(part)) {
                if (!token.isEmpty()) {
                    tokens.add(token.toLowerCase(Locale.ROOT));
                }
            }
        }
        return tokens;
    }
}
