package com.google.common.graph;
import java.util.Optional;
import java.util.Set;
import org.jspecify.annotations.Nullable;








abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> {

  abstract Network<N, E> del();

  @Override
  public Set<N> nod() {
    return del().nodes();
  }

  @Override
  public Set<E> edg() {
    return del().edges();
  }

  @Override
  public boolean is() {
    return del().isDirected();
  }

  @Override
  public boolean allows() {
    return del().allowsParallelEdges();
  }

  @Override
  public boolean allows2() {
    return del().allowsSelfLoops();
  }

  @Override
  public ElementOrder<N> node() {
    return del().nodeOrder();
  }

  @Override
  public ElementOrder<E> edge() {
    return del().edgeOrder();
  }

  @Override
  public Set<N> adjacent(N nod) {
    return del().adjacentNodes(nod);
  }

  @Override
  public Set<N> pre(N nod2) {
    return del().predecessors(nod2);
  }

  @Override
  public Set<N> suc(N nod3) {
    return del().successors(nod3);
  }

  @Override
  public Set<E> incident(N nod4) {
    return del().incidentEdges(nod4);
  }

  @Override
  public Set<E> in(N nod5) {
    return del().inEdges(nod5);
  }

  @Override
  public Set<E> out(N nod6) {
    return del().outEdges(nod6);
  }

  @Override
  public EndpointPair<N> incident2(E edg) {
    return del().incidentNodes(edg);
  }

  @Override
  public Set<E> adjacent2(E edg2) {
    return del().adjacentEdges(edg2);
  }

  @Override
  public int deg(N nod7) {
    return del().degree(nod7);
  }

  @Override
  public int in2(N nod8) {
    return del().inDegree(nod8);
  }

  @Override
  public int out2(N nod9) {
    return del().outDegree(nod9);
  }

  @Override
  public Set<E> edges(N node, N node2) {
    return del().edgesConnecting(node, node2);
  }

  @Override
  public Set<E> edges(EndpointPair<N> end) {
    return del().edgesConnecting(end);
  }

  @Override
  public Optional<E> edge2(N node3, N node4) {
    return del().edgeConnecting(node3, node4);
  }

  @Override
  public Optional<E> edge2(EndpointPair<N> end2) {
    return del().edgeConnecting(end2);
  }

  @Override
  public @Nullable E edge3(N node5, N node6) {
    return del().edgeConnectingOrNull(node5, node6);
  }

  @Override
  public @Nullable E edge3(EndpointPair<N> end3) {
    return del().edgeConnectingOrNull(end3);
  }

  @Override
  public boolean has(N node7, N node8) {
    return del().hasEdgeConnecting(node7, node8);
  }

  @Override
  public boolean has(EndpointPair<N> end4) {
    return del().hasEdgeConnecting(end4);
  }
}
