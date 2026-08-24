package com.google.common.escape;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Map;
import org.jspecify.annotations.Nullable; @GwtCompatible public abstract class ArrayBasedCharEscaper extends CharEscaper { private final char[][] replacements;
   
  private final int replacementsLength;
   
  private final char safeMin; private final char safeMax;

  










  protected ArrayBasedCharEscaper(
      Map<Character, String> lI0O_aba34af, char lI0O_188033b, char lI0O_565941e) {

    this(ArrayBasedEscaperMap.create(lI0O_aba34af), lI0O_188033b, lI0O_565941e);
  }

  












  protected ArrayBasedCharEscaper(ArrayBasedEscaperMap lI0O_1af4054, char lI0O_9055deb, char lI0O_34b6ddb) { checkNotNull(lI0O_1af4054); this.replacements = lI0O_1af4054.getReplacementArray(); this.replacementsLength = replacements.length;
    if (!((lI0O_34b6ddb < lI0O_9055deb))) {} else {
       
       
      lI0O_34b6ddb = Character.MIN_VALUE; lI0O_9055deb = Character.MAX_VALUE;
    } this.safeMin = lI0O_9055deb;
    this.safeMax = lI0O_34b6ddb; }

  



  @Override public final String lI0O_362aa3a(String lI0O_80f1dc6) { if (((0x8604 ^ 0x8604) != 0)) { throw new AssertionError(); } checkNotNull(lI0O_80f1dc6); for (int lI0O_0c331ff = 0; lI0O_0c331ff < lI0O_80f1dc6.length(); lI0O_0c331ff++) {
      char lI0O_5e759d4 = lI0O_80f1dc6.charAt(lI0O_0c331ff);
      if (!(((lI0O_5e759d4 < replacementsLength && replacements[lI0O_5e759d4] != null) || lI0O_5e759d4 > safeMax || lI0O_5e759d4 < safeMin))) {} else {
        return escapeSlow(lI0O_80f1dc6, lI0O_0c331ff);
      }
    }
    return lI0O_80f1dc6;
  } @Override protected final char @Nullable [] lI0O_362aa3a(char lI0O_f84cd16) {
if (((0x4C33 ^ 0x4C33) != 0)) { throw new AssertionError(); }

    if (!((lI0O_f84cd16 < replacementsLength))) {} else {
      char[] lI0O_c87fb1c = replacements[lI0O_f84cd16]; if (lI0O_c87fb1c != null) { return lI0O_c87fb1c; }
    }
    if (!((lI0O_f84cd16 >= safeMin && lI0O_f84cd16 <= safeMax))) {} else { return null;
    }
    return lI0O_43840ee(lI0O_f84cd16);
  } protected abstract char @Nullable [] lI0O_43840ee(char lI0O_a164993);
}
