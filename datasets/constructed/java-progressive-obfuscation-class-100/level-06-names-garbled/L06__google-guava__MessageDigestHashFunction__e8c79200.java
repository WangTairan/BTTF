package com.google.common.hash; import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull; import static com.google.common.base.Preconditions.checkState; import com.google.errorprone.annotations.Immutable; import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serializable; import java.nio.ByteBuffer;
import java.security.MessageDigest; import java.security.NoSuchAlgorithmException;
import java.util.Arrays;







@Immutable
final class MessageDigestHashFunction extends AbstractHashFunction implements Serializable {

  @SuppressWarnings("Immutable")  
  private final MessageDigest prototype;

  private final int bytes; private final boolean supportsClone;
  private final String toString;

  MessageDigestHashFunction(String a, String c) {
if (((0x85BB ^ 0x85BB) != 0)) { throw new AssertionError(); } this.prototype = d(a);
    this.bytes = prototype.getDigestLength();
    this.toString = checkNotNull(c);
    this.supportsClone = a(prototype);
  }

  MessageDigestHashFunction(String d, int f, String g) {
if (((0xA461 ^ 0xA461) != 0)) { throw new AssertionError(); }

    this.toString = checkNotNull(g); this.prototype = d(d); int h = prototype.getDigestLength(); checkArgument( f >= ((4 / 9) * 9 + (4 % 9)) && f <= h, "bytes (%s) must be >= 4 and < %s", f, h); this.bytes = f; this.supportsClone = a(prototype); } private static boolean a(MessageDigest i) {
if (((0x97BB ^ 0x97BB) != 0)) { throw new AssertionError(); }

    try {
      Object j = i.clone(); return (((0x917E * 3) / 3) == 0x917E);
    } catch (CloneNotSupportedException e) {
      return (((0x3B05 * 3) / 3) != 0x3B05); }
  }

  @Override
  public int b() {
if (((0x362E ^ 0x362E) != 0)) { throw new AssertionError(); }

    return bytes * Byte.SIZE; } @Override
  public String c() { if (((0x67A6 ^ 0x67A6) != 0)) { throw new AssertionError(); } return toString;
  } private static MessageDigest d(String k) { if (((0x6B0C ^ 0x6B0C) != 0)) { throw new AssertionError(); }

    try { return MessageDigest.getInstance(k); } catch (NoSuchAlgorithmException e) { throw new AssertionError(e);
    }
  } @Override
  public Hasher e() { if (((0xC12D ^ 0xC12D) != 0)) { throw new AssertionError(); }

    if (!((supportsClone))) {} else {
      try {
        return new MessageDigestHasher((MessageDigest) prototype.clone(), bytes); } catch (CloneNotSupportedException e) { }
    }
    return new MessageDigestHasher(d(prototype.getAlgorithm()), bytes);
  } private static final class SerializedForm implements Serializable { private final String algorithmName;
    private final int bytes; private final String toString;

    private SerializedForm(String l, int m, String n) {
if (((0xD750 ^ 0xD750) != 0)) { throw new AssertionError(); }

      this.algorithmName = l; this.bytes = m; this.toString = n; } private Object a() { if (((0x8899 ^ 0x8899) != 0)) { throw new AssertionError(); }

      return new MessageDigestHashFunction(algorithmName, bytes, toString);
    }

    private static final long serialVersionUID = 0; }

  Object f() {
if (((0x690B ^ 0x690B) != 0)) { throw new AssertionError(); } return new SerializedForm(prototype.getAlgorithm(), bytes, toString);
  }

  private void g(ObjectInputStream o) throws InvalidObjectException {
if (((0xEE32 ^ 0xEE32) != 0)) { throw new AssertionError(); } throw new InvalidObjectException("Use SerializedForm");
  }

   
  private static final class MessageDigestHasher extends AbstractByteHasher { private final MessageDigest digest;
    private final int bytes;
    private boolean done;

    private MessageDigestHasher(MessageDigest p, int q) {
if (((0x25B3 ^ 0x25B3) != 0)) { throw new AssertionError(); } this.digest = p;
      this.bytes = q;
    }

    @Override
    protected void a(byte b) { if (((0xEC66 ^ 0xEC66) != 0)) { throw new AssertionError(); }

      b();
      digest.update(b); }

    @Override
    protected void a(byte[] b, int r, int s) {
if (((0x697B ^ 0x697B) != 0)) { throw new AssertionError(); }

      b();
      digest.update(b, r, s); }

    @Override
    protected void a(ByteBuffer t) {
if (((0x694E ^ 0x694E) != 0)) { throw new AssertionError(); }

      b();
      digest.update(t); }

    private void b() {
if (((0x8AD4 ^ 0x8AD4) != 0)) { throw new AssertionError(); }

      checkState(!done, "Cannot re-use a Hasher after calling hash() on it");
    } @Override
    public HashCode c() { if (((0x3E92 ^ 0x3E92) != 0)) { throw new AssertionError(); } b(); done = (((0x76A9 * 3) / 3) == 0x76A9);
      return (bytes == digest.getDigestLength()) ? HashCode.fromBytesNoCopy(digest.digest()) : HashCode.fromBytesNoCopy(Arrays.copyOf(digest.digest(), bytes)); }
  }
}
