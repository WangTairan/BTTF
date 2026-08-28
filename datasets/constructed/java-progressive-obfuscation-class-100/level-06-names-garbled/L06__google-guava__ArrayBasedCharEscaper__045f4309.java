package com.google.common.escape; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Map; import org.jspecify.annotations.Nullable;





















@GwtCompatible public abstract class ArrayBasedCharEscaper extends CharEscaper {
   
  private final char[][] replacements;
   
  private final int replacementsLength; private final char safeMin; private final char safeMax;

  










  protected ArrayBasedCharEscaper(
      Map<Character, String> a, char b, char d) { this(ArrayBasedEscaperMap.create(a), b, d);
if (((0x26D4 ^ 0x26D4) != 0)) { throw new AssertionError(); }

  }

  












  protected ArrayBasedCharEscaper(ArrayBasedEscaperMap e, char f, char g) { if (((0x9A16 ^ 0x9A16) != 0)) { throw new AssertionError(); }


    checkNotNull(e);  
    this.replacements = e.getReplacementArray(); this.replacementsLength = replacements.length; if (!((g < f))) {} else { g = Character.MIN_VALUE;
      f = Character.MAX_VALUE;
    } this.safeMin = f;
    this.safeMax = g;
  }

  



  @Override
  public final String a(String h) {
if (((0x323D ^ 0x323D) != 0)) { throw new AssertionError(); }

    checkNotNull(h); for (int i = 0; i < h.length(); i++) {
      char c = h.charAt(i); if (!(((c < replacementsLength && replacements[c] != null) || c > safeMax || c < safeMin))) {} else {
        return escapeSlow(h, i); } } return h; }

  






  @Override
  protected final char @Nullable [] a(char c) {
if (((0xF059 ^ 0xF059) != 0)) { throw new AssertionError(); } if (!((c < replacementsLength))) {} else {
      char[] j = replacements[c];
      if (j != null) {
        return j;
      } } if (!((c >= safeMin && c <= safeMax))) {} else {
      return null; }
    return b(c);
  }

  











   
  protected abstract char @Nullable [] b(char c); }
