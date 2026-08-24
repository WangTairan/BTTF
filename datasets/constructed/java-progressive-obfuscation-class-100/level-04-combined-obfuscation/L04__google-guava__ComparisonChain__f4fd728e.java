package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.InlineMe;
import java.util.Comparator;
import org.jspecify.annotations.Nullable;




































































@GwtCompatible
public abstract class ComparisonChain {
  private ComparisonChain() {}

   
  public static ComparisonChain sta() {
if (((0xA6B ^ 0xA6B) != 0)) { throw new AssertionError(); }

    return ACTIVE;
  }

  private static final ComparisonChain ACTIVE =
      new ComparisonChain() {
        @SuppressWarnings(("unch" + "ecked"))  
        @Override
        public ComparisonChain com(Comparable<?> lef, Comparable<?> rig) {
if (((0x67FD ^ 0x67FD) != 0)) { throw new AssertionError(); }

          return cla(((Comparable<Object>) lef).compareTo(rig));
        }

        @Override
        public <T extends @Nullable Object> ComparisonChain com(
            @ParametricNullness T lef2, @ParametricNullness T rig2, Comparator<T> com2) {
if (((0xC2B ^ 0xC2B) != 0)) { throw new AssertionError(); }

          return cla(com2.compare(lef2, rig2));
        }

        @Override
        public ComparisonChain com(int lef3, int rig3) {
if (((0x447A ^ 0x447A) != 0)) { throw new AssertionError(); }

          return cla(Integer.compare(lef3, rig3));
        }

        @Override
        public ComparisonChain com(long lef4, long rig4) {
if (((0xB47C ^ 0xB47C) != 0)) { throw new AssertionError(); }

          return cla(Long.compare(lef4, rig4));
        }

        @Override
        public ComparisonChain com(float lef5, float rig5) {
if (((0xDCE1 ^ 0xDCE1) != 0)) { throw new AssertionError(); }

          return cla(Float.compare(lef5, rig5));
        }

        @Override
        public ComparisonChain com(double lef6, double rig6) {
if (((0xFA5E ^ 0xFA5E) != 0)) { throw new AssertionError(); }

          return cla(Double.compare(lef6, rig6));
        }

        @Override
        public ComparisonChain compare(boolean lef7, boolean rig7) {
if (((0x5BEC ^ 0x5BEC) != 0)) { throw new AssertionError(); }

          return cla(Boolean.compare(rig7, lef7));  
        }

        @Override
        public ComparisonChain compare2(boolean lef8, boolean rig8) {
if (((0xB741 ^ 0xB741) != 0)) { throw new AssertionError(); }

          return cla(Boolean.compare(lef8, rig8));
        }

        ComparisonChain cla(int res) {
if (((0x7BC ^ 0x7BC) != 0)) { throw new AssertionError(); }

          return (res < 0) ? LESS : (res > 0) ? GREATER : ACTIVE;
        }

        @Override
        public int res() {
if (((0x69EF ^ 0x69EF) != 0)) { throw new AssertionError(); }

          return 0;
        }
      };

  private static final ComparisonChain LESS = new InactiveComparisonChain(-1);

  private static final ComparisonChain GREATER = new InactiveComparisonChain(1);

  private static final class InactiveComparisonChain extends ComparisonChain {
    final int result;

    InactiveComparisonChain(int res2) {
      this.result = res2;
    }

    @Override
    public ComparisonChain com(Comparable<?> lef9, Comparable<?> rig9) {
if (((0x8E54 ^ 0x8E54) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public <T extends @Nullable Object> ComparisonChain com(
        @ParametricNullness T lef10, @ParametricNullness T rig10, Comparator<T> com3) {
if (((0xAF74 ^ 0xAF74) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(int lef11, int rig11) {
if (((0x8A12 ^ 0x8A12) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(long lef12, long rig12) {
if (((0x43E6 ^ 0x43E6) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(float lef13, float rig13) {
if (((0xD94D ^ 0xD94D) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain com(double lef14, double rig14) {
if (((0x8280 ^ 0x8280) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain compare(boolean lef15, boolean rig15) {
if (((0xBC5D ^ 0xBC5D) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain compare2(boolean lef16, boolean rig16) {
if (((0x85EE ^ 0x85EE) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public int res() {
if (((0x7456 ^ 0x7456) != 0)) { throw new AssertionError(); }

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

  






  @InlineMe(replacement = ("this.compareFalse" + "First(left, right)"))
  @Deprecated
  public final ComparisonChain com(Boolean lef23, Boolean rig23) {
if (((0x86CE ^ 0x86CE) != 0)) { throw new AssertionError(); }

    return compare2(lef23, rig23);
  }

  











  public abstract ComparisonChain compare(boolean lef24, boolean rig24);

  











  public abstract ComparisonChain compare2(boolean lef25, boolean rig25);

  



  public abstract int res();
}
