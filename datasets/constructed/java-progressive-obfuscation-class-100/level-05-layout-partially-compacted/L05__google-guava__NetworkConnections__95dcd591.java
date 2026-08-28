package com.google.common.graph;
import com.google.errorprone.annotations.CanIgnoreReturnValue; import java.util.Set;
import org.jspecify.annotations.Nullable; interface NetworkConnections<N, E> { Set<N> adjacent();

  Set<N> pre();

  Set<N> suc(); Set<E> incident();

  Set<E> in();

  Set<E> out();

  



  Set<E> edges(N nod);

  




  N adjacent2(E edg);

  




  @CanIgnoreReturnValue @Nullable N remove(E edg2, boolean is); @CanIgnoreReturnValue N remove2(E edg3);

  


  void add(E edg4, N nod2, boolean is2);

   
  void add2(E edg5, N nod3);
}
