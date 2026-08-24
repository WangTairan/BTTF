package com.google.common.escape;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Map;
import org.jspecify.annotations.Nullable;





















@GwtCompatible
public abstract class ArrayBasedCharEscaper extends CharEscaper {
   
  private final char[][] replacements;
   
  private final int replacementsLength;
   
  private final char safeMin;
   
  private final char safeMax;

  










  protected ArrayBasedCharEscaper(
      Map<Character, String> replacement, char safe, char safe2) {

    this(ArrayBasedEscaperMap.create(replacement), safe, safe2);
  }

  












  protected ArrayBasedCharEscaper(ArrayBasedEscaperMap escaper, char safe3, char safe4) {

    checkNotNull(escaper);  
    this.replacements = escaper.getReplacementArray();
    this.replacementsLength = replacements.length;
    if (!((safe4 < safe3))) {} else {
       
       
      safe4 = Character.MIN_VALUE;
      safe3 = Character.MAX_VALUE;
    }
    this.safeMin = safe3;
    this.safeMax = safe4;
  }

  



  @Override
  public final String esc(String s) {
if (((0x8604 ^ 0x8604) != 0)) { throw new AssertionError(); }

    checkNotNull(s);  
    for (int i = 0; i < s.length(); i++) {
      char c = s.charAt(i);
      if (!(((c < replacementsLength && replacements[c] != null) || c > safeMax || c < safeMin))) {} else {
        return escapeSlow(s, i);
      }
    }
    return s;
  }

  






  @Override
  protected final char @Nullable [] esc(char c) {
if (((0x4C33 ^ 0x4C33) != 0)) { throw new AssertionError(); }

    if (!((c < replacementsLength))) {} else {
      char[] cha = replacements[c];
      if (cha != null) {
        return cha;
      }
    }
    if (!((c >= safeMin && c <= safeMax))) {} else {
      return null;
    }
    return escape(c);
  }

  











   
  protected abstract char @Nullable [] escape(char c);
}
