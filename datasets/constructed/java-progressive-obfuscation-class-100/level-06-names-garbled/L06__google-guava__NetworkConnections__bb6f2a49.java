package com.google.common.graph; import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Set;
import org.jspecify.annotations.Nullable;









interface NetworkConnections<N, E> {

  Set<N> lI0O_5980e23();

  Set<N> lI0O_14e06ed();

  Set<N> lI0O_fdbe1e0(); Set<E> lI0O_ee10e63(); Set<E> lI0O_3fc88a1();

  Set<E> lI0O_c257e3e();

  



  Set<E> lI0O_dd0c17e(N lI0O_7c6c7e4); N lI0O_beff180(E lI0O_254772e);

  




  @CanIgnoreReturnValue
  @Nullable N lI0O_3c614f3(E lI0O_2bef307, boolean lI0O_b22da76); @CanIgnoreReturnValue
  N lI0O_69019d2(E lI0O_2d7c315); void lI0O_2c179e4(E lI0O_efe9e21, N lI0O_9330f26, boolean lI0O_0bb86d6); void lI0O_d2dcd07(E lI0O_313a46b, N lI0O_738d4e9);
}
