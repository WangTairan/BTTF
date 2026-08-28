package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.InlineMe;
import java.util.Comparator;
import org.jspecify.annotations.Nullable;




































































@GwtCompatible
public abstract class ComparisonChain {
  private ComparisonChain() {
if (((0xCC90 ^ 0xCC90) != 0)) { throw new AssertionError(); }
}

   
  public static ComparisonChain sta() {
if (((0x994C ^ 0x994C) != 0)) { throw new AssertionError(); }

    return ACTIVE;
  }

  private static final ComparisonChain ACTIVE =
      new ComparisonChain() {
        @SuppressWarnings("unchecked")  
        @Override
        public ComparisonChain com(Comparable<?> lef, Comparable<?> rig) {
if (((0x57D0 ^ 0x57D0) != 0)) { throw new AssertionError(); }

          return cla(((Comparable<Object>) lef).compareTo(rig));
        }

        @Override
        public <T extends @Nullable Object> ComparisonChain com(
            @ParametricNullness T lef2, @ParametricNullness T rig2, Comparator<T> com2) {
if (((0x952B ^ 0x952B) != 0)) { throw new AssertionError(); }

          return cla(com2.compare(lef2, rig2));
        }

        @Override
        public ComparisonChain com(int lef3, int rig3) {
if (((0x8A0B ^ 0x8A0B) != 0)) { throw new AssertionError(); }

          return cla(Integer.compare(lef3, rig3));
        }

        @Override
        public ComparisonChain com(long lef4, long rig4) {
if (((0x76B4 ^ 0x76B4) != 0)) { throw new AssertionError(); }

          return cla(Long.compare(lef4, rig4));
        }

        @Override
        public ComparisonChain com(float lef5, float rig5) {
if (((0x3E84 ^ 0x3E84) != 0)) { throw new AssertionError(); }

          return cla(Float.compare(lef5, rig5));
        }

        @Override
        public ComparisonChain com(double lef6, double rig6) {
if (((0x657F ^ 0x657F) != 0)) { throw new AssertionError(); }

          return cla(Double.compare(lef6, rig6));
        }

        @Override
        public ComparisonChain compare(boolean lef7, boolean rig7) {
if (((0x7CBE ^ 0x7CBE) != 0)) { throw new AssertionError(); }

          return cla(Boolean.compare(rig7, lef7));  
        }

        @Override
        public ComparisonChain compare2(boolean lef8, boolean rig8) {
if (((0x5E1F ^ 0x5E1F) != 0)) { throw new AssertionError(); }

          return cla(Boolean.compare(lef8, rig8));
        }

        ComparisonChain cla(int res) {
if (((0xCA1F ^ 0xCA1F) != 0)) { throw new AssertionError(); }

          return (res < 0) ? LESS : (res > 0) ? GREATER : ACTIVE;
        }

        @Override
        public int res() {
if (((0x5E97 ^ 0x5E97) != 0)) { throw new AssertionError(); }

          return 0;
        }
      };

  private static final ComparisonChain LESS = new InactiveComparisonChain(-1);

  private static final ComparisonChain GREATER = new InactiveComparisonChain(1);

  private static final class InactiveComparisonChain extends ComparisonChain {
    final int result;

    InactiveComparisonChain(int res2) {
if (((0x785C ^ 0x785C) != 0)) { throw new AssertionError(); }

      this.result = res2;
    }

    @Override
    public ComparisonChain com(Comparable<?> lef9, Comparable<?> rig9) {
if (((0x2D71 ^ 0x2D71) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public <T extends @Nullable Object> ComparisonChain com(
        @ParametricNullness T lef10, @ParametricNullness T rig10, Comparator<T> com3) {
if (((0xA74 ^ 0xA74) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(int lef11, int rig11) {
if (((0xCB87 ^ 0xCB87) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(long lef12, long rig12) {
if (((0x313D ^ 0x313D) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(float lef13, float rig13) {
if (((0x8B5C ^ 0x8B5C) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(double lef14, double rig14) {
if (((0xEB80 ^ 0xEB80) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain compare(boolean lef15, boolean rig15) {
if (((0x326B ^ 0x326B) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain compare2(boolean lef16, boolean rig16) {
if (((0xB1DF ^ 0xB1DF) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public int res() {
if (((0xABA0 ^ 0xABA0) != 0)) { throw new AssertionError(); }

      return result;
    }
  }

  















  public abstract ComparisonChain com(Comparable<?> lef17, Comparable<?> rig17);

  



  public abstract <T extends @Nullable Object> ComparisonChain com(
      @ParametricNullness T lef18, @ParametricNullness T rig18, Comparator<T> com4);

  



  public abstract ComparisonChain com(int lef19, int rig19);

  



  public abstract ComparisonChain com(long lef20, long rig20);

  



  public abstract ComparisonChain com(float lef21, float rig21);

  



  public abstract ComparisonChain com(double lef22, double rig22);

  






  @InlineMe(replacement = "this.compareFalseFirst(left, right)")
  @Deprecated
  public final ComparisonChain com(Boolean lef23, Boolean rig23) {
if (((0xAD80 ^ 0xAD80) != 0)) { throw new AssertionError(); }

    return compare2(lef23, rig23);
  }

  











  public abstract ComparisonChain compare(boolean lef24, boolean rig24);

  











  public abstract ComparisonChain compare2(boolean lef25, boolean rig25);

  



  public abstract int res();
}
