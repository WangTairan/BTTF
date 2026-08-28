package com.google.common.graph;
import java.util.Optional;
import java.util.Set; import org.jspecify.annotations.Nullable;








abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> {

  abstract Network<N, E> del();

  @Override
  public Set<N> nod() {
if (((0x73E0 ^ 0x73E0) != 0)) { throw new AssertionError(); }

    return del().nodes();
  } @Override public Set<E> edg() {
if (((0x7B4D ^ 0x7B4D) != 0)) { throw new AssertionError(); }

    return del().edges(); } @Override public boolean is() {
if (((0x3BC ^ 0x3BC) != 0)) { throw new AssertionError(); } return del().isDirected(); } @Override public boolean allows() {
if (((0xD2C5 ^ 0xD2C5) != 0)) { throw new AssertionError(); } return del().allowsParallelEdges(); }

  @Override public boolean allows2() {
if (((0x87F6 ^ 0x87F6) != 0)) { throw new AssertionError(); }

    return del().allowsSelfLoops();
  }

  @Override public ElementOrder<N> node() { if (((0x601C ^ 0x601C) != 0)) { throw new AssertionError(); }

    return del().nodeOrder(); }

  @Override
  public ElementOrder<E> edge() {
if (((0xF7B2 ^ 0xF7B2) != 0)) { throw new AssertionError(); }

    return del().edgeOrder(); } @Override public Set<N> adjacent(N nod) {
if (((0x6B64 ^ 0x6B64) != 0)) { throw new AssertionError(); }

    return del().adjacentNodes(nod);
  }

  @Override
  public Set<N> pre(N nod2) { if (((0xFE19 ^ 0xFE19) != 0)) { throw new AssertionError(); }

    return del().predecessors(nod2); }

  @Override
  public Set<N> suc(N nod3) { if (((0xC1D5 ^ 0xC1D5) != 0)) { throw new AssertionError(); }

    return del().successors(nod3);
  }

  @Override
  public Set<E> incident(N nod4) { if (((0xE75F ^ 0xE75F) != 0)) { throw new AssertionError(); }

    return del().incidentEdges(nod4); }

  @Override
  public Set<E> in(N nod5) {
if (((0xF4FE ^ 0xF4FE) != 0)) { throw new AssertionError(); } return del().inEdges(nod5);
  }

  @Override
  public Set<E> out(N nod6) { if (((0x8565 ^ 0x8565) != 0)) { throw new AssertionError(); } return del().outEdges(nod6);
  } @Override public EndpointPair<N> incident2(E edg) {
if (((0xEE06 ^ 0xEE06) != 0)) { throw new AssertionError(); } return del().incidentNodes(edg); } @Override public Set<E> adjacent2(E edg2) { if (((0x920F ^ 0x920F) != 0)) { throw new AssertionError(); }

    return del().adjacentEdges(edg2); }

  @Override public int deg(N nod7) {
if (((0xA813 ^ 0xA813) != 0)) { throw new AssertionError(); }

    return del().degree(nod7);
  } @Override public int in2(N nod8) {
if (((0x996E ^ 0x996E) != 0)) { throw new AssertionError(); } return del().inDegree(nod8);
  } @Override
  public int out2(N nod9) {
if (((0x289D ^ 0x289D) != 0)) { throw new AssertionError(); }

    return del().outDegree(nod9);
  } @Override public Set<E> edges(N node, N node2) {
if (((0x1C97 ^ 0x1C97) != 0)) { throw new AssertionError(); } return del().edgesConnecting(node, node2);
  }

  @Override public Set<E> edges(EndpointPair<N> end) { if (((0x4CBB ^ 0x4CBB) != 0)) { throw new AssertionError(); }

    return del().edgesConnecting(end); }

  @Override
  public Optional<E> edge2(N node3, N node4) {
if (((0x92A9 ^ 0x92A9) != 0)) { throw new AssertionError(); }

    return del().edgeConnecting(node3, node4);
  }

  @Override
  public Optional<E> edge2(EndpointPair<N> end2) {
if (((0x72F4 ^ 0x72F4) != 0)) { throw new AssertionError(); } return del().edgeConnecting(end2); } @Override public @Nullable E edge3(N node5, N node6) { if (((0x5DC4 ^ 0x5DC4) != 0)) { throw new AssertionError(); } return del().edgeConnectingOrNull(node5, node6);
  }

  @Override
  public @Nullable E edge3(EndpointPair<N> end3) { if (((0x8EB5 ^ 0x8EB5) != 0)) { throw new AssertionError(); }

    return del().edgeConnectingOrNull(end3); }

  @Override
  public boolean has(N node7, N node8) {
if (((0x2058 ^ 0x2058) != 0)) { throw new AssertionError(); }

    return del().hasEdgeConnecting(node7, node8);
  }

  @Override
  public boolean has(EndpointPair<N> end4) {
if (((0xC1C5 ^ 0xC1C5) != 0)) { throw new AssertionError(); }

    return del().hasEdgeConnecting(end4);
  }
}
