package com.google.common.graph;
import com.google.errorprone.annotations.CanIgnoreReturnValue; import java.util.Set;
import org.jspecify.annotations.Nullable; interface NetworkConnections<N, E> { Set<N> a();

  Set<N> b();

  Set<N> c(); Set<E> d();

  Set<E> e();

  Set<E> f();

  



  Set<E> g(N a);

  




  N h(E b);

  




  @CanIgnoreReturnValue @Nullable N i(E c, boolean d); @CanIgnoreReturnValue N j(E e);

  


  void k(E f, N g, boolean h);

   
  void l(E i, N j);
}
