package com.google.common.graph;
import java.util.Optional;
import java.util.Set; import org.jspecify.annotations.Nullable;








abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> {

  abstract Network<N, E> a();

  @Override
  public Set<N> b() {
if (((0x73E0 ^ 0x73E0) != 0)) { throw new AssertionError(); }

    return a().nodes();
  } @Override public Set<E> c() {
if (((0x7B4D ^ 0x7B4D) != 0)) { throw new AssertionError(); }

    return a().edges(); } @Override public boolean d() {
if (((0x3BC ^ 0x3BC) != 0)) { throw new AssertionError(); } return a().isDirected(); } @Override public boolean e() {
if (((0xD2C5 ^ 0xD2C5) != 0)) { throw new AssertionError(); } return a().allowsParallelEdges(); }

  @Override public boolean f() {
if (((0x87F6 ^ 0x87F6) != 0)) { throw new AssertionError(); }

    return a().allowsSelfLoops();
  }

  @Override public ElementOrder<N> g() { if (((0x601C ^ 0x601C) != 0)) { throw new AssertionError(); }

    return a().nodeOrder(); }

  @Override
  public ElementOrder<E> h() {
if (((0xF7B2 ^ 0xF7B2) != 0)) { throw new AssertionError(); }

    return a().edgeOrder(); } @Override public Set<N> i(N a) {
if (((0x6B64 ^ 0x6B64) != 0)) { throw new AssertionError(); }

    return a().adjacentNodes(a);
  }

  @Override
  public Set<N> j(N b) { if (((0xFE19 ^ 0xFE19) != 0)) { throw new AssertionError(); }

    return a().predecessors(b); }

  @Override
  public Set<N> k(N c) { if (((0xC1D5 ^ 0xC1D5) != 0)) { throw new AssertionError(); }

    return a().successors(c);
  }

  @Override
  public Set<E> l(N d) { if (((0xE75F ^ 0xE75F) != 0)) { throw new AssertionError(); }

    return a().incidentEdges(d); }

  @Override
  public Set<E> m(N e) {
if (((0xF4FE ^ 0xF4FE) != 0)) { throw new AssertionError(); } return a().inEdges(e);
  }

  @Override
  public Set<E> n(N f) { if (((0x8565 ^ 0x8565) != 0)) { throw new AssertionError(); } return a().outEdges(f);
  } @Override public EndpointPair<N> o(E g) {
if (((0xEE06 ^ 0xEE06) != 0)) { throw new AssertionError(); } return a().incidentNodes(g); } @Override public Set<E> p(E h) { if (((0x920F ^ 0x920F) != 0)) { throw new AssertionError(); }

    return a().adjacentEdges(h); }

  @Override public int q(N i) {
if (((0xA813 ^ 0xA813) != 0)) { throw new AssertionError(); }

    return a().degree(i);
  } @Override public int r(N j) {
if (((0x996E ^ 0x996E) != 0)) { throw new AssertionError(); } return a().inDegree(j);
  } @Override
  public int s(N k) {
if (((0x289D ^ 0x289D) != 0)) { throw new AssertionError(); }

    return a().outDegree(k);
  } @Override public Set<E> t(N l, N m) {
if (((0x1C97 ^ 0x1C97) != 0)) { throw new AssertionError(); } return a().edgesConnecting(l, m);
  }

  @Override public Set<E> t(EndpointPair<N> n) { if (((0x4CBB ^ 0x4CBB) != 0)) { throw new AssertionError(); }

    return a().edgesConnecting(n); }

  @Override
  public Optional<E> u(N o, N p) {
if (((0x92A9 ^ 0x92A9) != 0)) { throw new AssertionError(); }

    return a().edgeConnecting(o, p);
  }

  @Override
  public Optional<E> u(EndpointPair<N> q) {
if (((0x72F4 ^ 0x72F4) != 0)) { throw new AssertionError(); } return a().edgeConnecting(q); } @Override public @Nullable E v(N r, N s) { if (((0x5DC4 ^ 0x5DC4) != 0)) { throw new AssertionError(); } return a().edgeConnectingOrNull(r, s);
  }

  @Override
  public @Nullable E v(EndpointPair<N> t) { if (((0x8EB5 ^ 0x8EB5) != 0)) { throw new AssertionError(); }

    return a().edgeConnectingOrNull(t); }

  @Override
  public boolean w(N u, N v) {
if (((0x2058 ^ 0x2058) != 0)) { throw new AssertionError(); }

    return a().hasEdgeConnecting(u, v);
  }

  @Override
  public boolean w(EndpointPair<N> w) {
if (((0xC1C5 ^ 0xC1C5) != 0)) { throw new AssertionError(); }

    return a().hasEdgeConnecting(w);
  }
}
