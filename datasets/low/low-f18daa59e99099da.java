package org.apache.commons.codec.language;
import java.util.regex.Pattern;
import org.apache.commons.codec.EncoderException;
import org.apache.commons.codec.StringEncoder;

/* loaded from: Nysiis.class */
public class Nysiis implements StringEncoder {
    private static final char[] CHARS_A = {'A'};
    private static final char[] CHARS_AF = {'A', 'F'};
    private static final char[] CHARS_C = {'C'};
    private static final char[] CHARS_FF = {'F', 'F'};
    private static final char[] CHARS_G = {'G'};
    private static final char[] CHARS_N = {'N'};
    private static final char[] CHARS_NN = {'N', 'N'};
    private static final char[] CHARS_S = {'S'};
    private static final char[] CHARS_SSS = {'S', 'S', 'S'};
    private static final Pattern PAT_MAC = Pattern.compile("^MAC");
    private static final Pattern PAT_KN = Pattern.compile("^KN");
    private static final Pattern PAT_K = Pattern.compile("^K");
    private static final Pattern PAT_PH_PF = Pattern.compile("^(PH|PF)");
    private static final Pattern PAT_SCH = Pattern.compile("^SCH");
    private static final Pattern PAT_EE_IE = Pattern.compile("(EE|IE)$");
    private static final Pattern PAT_DT_ETC = Pattern.compile("(DT|RT|RD|NT|ND)$");
    private static final char SPACE = ' ';
    private static final int TRUE_LENGTH = 6;
    private final boolean strict;

    private static boolean isVowel(char c) {
        return c == 'A' || c == 'E' || c == 'I' || c == 'O' || c == 'U';
    }

    private static char[] transcodeRemaining(char prev, char curr, char next, char aNext) {
        if (curr == 'E' && next == 'V') {
            return CHARS_AF;
        }
        if (isVowel(curr)) {
            return CHARS_A;
        }
        if (curr == 'Q') {
            return CHARS_G;
        }
        if (curr == 'Z') {
            return CHARS_S;
        }
        if (curr == 'M') {
            return CHARS_N;
        }
        if (curr == 'K') {
            if (next == 'N') {
                return CHARS_NN;
            }
            return CHARS_C;
        } else if (curr == 'S' && next == 'C' && aNext == 'H') {
            return CHARS_SSS;
        } else {
            if (curr == 'P' && next == 'H') {
                return CHARS_FF;
            }
            return (curr != 'H' || (isVowel(prev) && isVowel(next))) ? (curr == 'W' && isVowel(prev)) ? new char[]{prev} : new char[]{curr} : new char[]{prev};
        }
    }

    public Nysiis() {
        this(true);
    }

    public Nysiis(boolean strict) {
        this.strict = strict;
    }

    @Override // org.apache.commons.codec.Encoder
    public Object encode(Object obj) throws EncoderException {
        if (!(obj instanceof String)) {
            throw new EncoderException("Parameter supplied to Nysiis encode is not of type java.lang.String");
        }
        return nysiis((String) obj);
    }

    @Override // org.apache.commons.codec.StringEncoder
    public String encode(String str) {
        return nysiis(str);
    }

    public boolean isStrict() {
        return this.strict;
    }

    public String nysiis(String str) {
        if (str == null) {
            return null;
        }
        String str2 = SoundexUtils.clean(str);
        if (str2.length() == 0) {
            return str2;
        }
        String str3 = PAT_DT_ETC.matcher(PAT_EE_IE.matcher(PAT_SCH.matcher(PAT_PH_PF.matcher(PAT_K.matcher(PAT_KN.matcher(PAT_MAC.matcher(str2).replaceFirst("MCC")).replaceFirst("NN")).replaceFirst("C")).replaceFirst("FF")).replaceFirst("SSS")).replaceFirst("Y")).replaceFirst("D");
        StringBuilder key = new StringBuilder(str3.length());
        key.append(str3.charAt(0));
        char[] chars = str3.toCharArray();
        int len = chars.length;
        int i = 1;
        while (i < len) {
            char next = i < len - 1 ? chars[i + 1] : ' ';
            char aNext = i < len - 2 ? chars[i + 2] : ' ';
            char[] transcoded = transcodeRemaining(chars[i - 1], chars[i], next, aNext);
            System.arraycopy(transcoded, 0, chars, i, transcoded.length);
            if (chars[i] != chars[i - 1]) {
                key.append(chars[i]);
            }
            i++;
        }
        if (key.length() > 1) {
            char lastChar = key.charAt(key.length() - 1);
            if (lastChar == 'S') {
                key.deleteCharAt(key.length() - 1);
                lastChar = key.charAt(key.length() - 1);
            }
            if (key.length() > 2) {
                char last2Char = key.charAt(key.length() - 2);
                if (last2Char == 'A' && lastChar == 'Y') {
                    key.deleteCharAt(key.length() - 2);
                }
            }
            if (lastChar == 'A') {
                key.deleteCharAt(key.length() - 1);
            }
        }
        String string = key.toString();
        return isStrict() ? string.substring(0, Math.min((int) TRUE_LENGTH, string.length())) : string;
    }
}
