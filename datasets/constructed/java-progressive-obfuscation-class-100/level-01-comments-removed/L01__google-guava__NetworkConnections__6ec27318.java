package com.google.common.graph;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Set;
import org.jspecify.annotations.Nullable;









interface NetworkConnections<N, E> {

  Set<N> adjacentNodes();

  Set<N> predecessors();

  Set<N> successors();

  Set<E> incidentEdges();

  Set<E> inEdges();

  Set<E> outEdges();

  



  Set<E> edgesConnecting(N node);

  




  N adjacentNode(E edge);

  




  @CanIgnoreReturnValue
  @Nullable N removeInEdge(E edge, boolean isSelfLoop);

   
  @CanIgnoreReturnValue
  N removeOutEdge(E edge);

  


  void addInEdge(E edge, N node, boolean isSelfLoop);

   
  void addOutEdge(E edge, N node);
}
