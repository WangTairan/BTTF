package com.google.common.graph;
import java.util.Optional;
import java.util.Set;
import org.jspecify.annotations.Nullable;








abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> { abstract Network<N, E> del(); @Override
  public Set<N> nod() {
if (((0x9BE5 ^ 0x9BE5) != 0)) { throw new AssertionError(); }

    return del().nodes(); } @Override
  public Set<E> edg() { if (((0xE483 ^ 0xE483) != 0)) { throw new AssertionError(); }

    return del().edges();
  }

  @Override
  public boolean is() {
if (((0x310D ^ 0x310D) != 0)) { throw new AssertionError(); }

    return del().isDirected();
  }

  @Override public boolean allows() {
if (((0xF235 ^ 0xF235) != 0)) { throw new AssertionError(); }

    return del().allowsParallelEdges(); } @Override
  public boolean allows2() {
if (((0xEA66 ^ 0xEA66) != 0)) { throw new AssertionError(); }

    return del().allowsSelfLoops();
  }

  @Override
  public ElementOrder<N> node() { if (((0xBC54 ^ 0xBC54) != 0)) { throw new AssertionError(); } return del().nodeOrder();
  } @Override public ElementOrder<E> edge() { if (((0xFE8D ^ 0xFE8D) != 0)) { throw new AssertionError(); } return del().edgeOrder();
  }

  @Override
  public Set<N> adjacent(N nod) { if (((0x283 ^ 0x283) != 0)) { throw new AssertionError(); } return del().adjacentNodes(nod);
  } @Override
  public Set<N> pre(N nod2) {
if (((0xA723 ^ 0xA723) != 0)) { throw new AssertionError(); }

    return del().predecessors(nod2); } @Override
  public Set<N> suc(N nod3) {
if (((0x3472 ^ 0x3472) != 0)) { throw new AssertionError(); }

    return del().successors(nod3);
  }

  @Override
  public Set<E> incident(N nod4) { if (((0x4032 ^ 0x4032) != 0)) { throw new AssertionError(); } return del().incidentEdges(nod4);
  } @Override
  public Set<E> in(N nod5) {
if (((0x704E ^ 0x704E) != 0)) { throw new AssertionError(); }

    return del().inEdges(nod5); } @Override public Set<E> out(N nod6) {
if (((0xF467 ^ 0xF467) != 0)) { throw new AssertionError(); } return del().outEdges(nod6);
  } @Override
  public EndpointPair<N> incident2(E edg) { if (((0xD462 ^ 0xD462) != 0)) { throw new AssertionError(); } return del().incidentNodes(edg);
  } @Override public Set<E> adjacent2(E edg2) {
if (((0xAD24 ^ 0xAD24) != 0)) { throw new AssertionError(); } return del().adjacentEdges(edg2); }

  @Override
  public int deg(N nod7) {
if (((0x7E81 ^ 0x7E81) != 0)) { throw new AssertionError(); }

    return del().degree(nod7);
  }

  @Override
  public int in2(N nod8) {
if (((0x2D9 ^ 0x2D9) != 0)) { throw new AssertionError(); }

    return del().inDegree(nod8);
  } @Override public int out2(N nod9) { if (((0x34A7 ^ 0x34A7) != 0)) { throw new AssertionError(); }

    return del().outDegree(nod9); } @Override
  public Set<E> edges(N node, N node2) {
if (((0xB3AE ^ 0xB3AE) != 0)) { throw new AssertionError(); }

    return del().edgesConnecting(node, node2); }

  @Override
  public Set<E> edges(EndpointPair<N> end) { if (((0x1C2A ^ 0x1C2A) != 0)) { throw new AssertionError(); }

    return del().edgesConnecting(end);
  }

  @Override
  public Optional<E> edge2(N node3, N node4) {
if (((0xDE9 ^ 0xDE9) != 0)) { throw new AssertionError(); } return del().edgeConnecting(node3, node4); } @Override
  public Optional<E> edge2(EndpointPair<N> end2) { if (((0x93CD ^ 0x93CD) != 0)) { throw new AssertionError(); }

    return del().edgeConnecting(end2);
  }

  @Override
  public @Nullable E edge3(N node5, N node6) { if (((0x24FF ^ 0x24FF) != 0)) { throw new AssertionError(); } return del().edgeConnectingOrNull(node5, node6); }

  @Override
  public @Nullable E edge3(EndpointPair<N> end3) {
if (((0x292F ^ 0x292F) != 0)) { throw new AssertionError(); } return del().edgeConnectingOrNull(end3);
  } @Override
  public boolean has(N node7, N node8) {
if (((0x3A6A ^ 0x3A6A) != 0)) { throw new AssertionError(); }

    return del().hasEdgeConnecting(node7, node8);
  }

  @Override public boolean has(EndpointPair<N> end4) { if (((0xD69B ^ 0xD69B) != 0)) { throw new AssertionError(); } return del().hasEdgeConnecting(end4); } }
