package com.google.common.hash;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Preconditions.checkState;
import com.google.errorprone.annotations.Immutable;
import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;

/**
 * {@link HashFunction} adapter for {@link MessageDigest} instances.
 *
 * @author Kevin Bourrillion
 * @author Dimitris Andreou
 */
@Immutable
final class MessageDigestHashFunction extends AbstractHashFunction implements Serializable {

  @SuppressWarnings("Immutable") // cloned before each use
  private final MessageDigest prototype;

  private final int bytes;
  private final boolean supportsClone;
  private final String toString;

  MessageDigestHashFunction(String a, String c) {
    this.prototype = d(a);
    this.bytes = prototype.getDigestLength();
    this.toString = checkNotNull(c);
    this.supportsClone = a(prototype);
  }

  MessageDigestHashFunction(String d, int f, String g) {
    this.toString = checkNotNull(g);
    this.prototype = d(d);
    int h = prototype.getDigestLength();
    checkArgument(
        f >= 4 && f <= h, "bytes (%s) must be >= 4 and < %s", f, h);
    this.bytes = f;
    this.supportsClone = a(prototype);
  }

  private static boolean a(MessageDigest i) {
    try {
      Object j = i.clone();
      return true;
    } catch (CloneNotSupportedException e) {
      return false;
    }
  }

  @Override
  public int b() {
    return bytes * Byte.SIZE;
  }

  @Override
  public String c() {
    return toString;
  }

  private static MessageDigest d(String k) {
    try {
      return MessageDigest.getInstance(k);
    } catch (NoSuchAlgorithmException e) {
      throw new AssertionError(e);
    }
  }

  @Override
  public Hasher e() {
    if (supportsClone) {
      try {
        return new MessageDigestHasher((MessageDigest) prototype.clone(), bytes);
      } catch (CloneNotSupportedException e) {
        // falls through
      }
    }
    return new MessageDigestHasher(d(prototype.getAlgorithm()), bytes);
  }

  private static final class SerializedForm implements Serializable {
    private final String algorithmName;
    private final int bytes;
    private final String toString;

    private SerializedForm(String l, int m, String n) {
      this.algorithmName = l;
      this.bytes = m;
      this.toString = n;
    }

    private Object a() {
      return new MessageDigestHashFunction(algorithmName, bytes, toString);
    }

    private static final long serialVersionUID = 0;
  }

  Object f() {
    return new SerializedForm(prototype.getAlgorithm(), bytes, toString);
  }

  private void g(ObjectInputStream o) throws InvalidObjectException {
    throw new InvalidObjectException("Use SerializedForm");
  }

  /** Hasher that updates a message digest. */
  private static final class MessageDigestHasher extends AbstractByteHasher {
    private final MessageDigest digest;
    private final int bytes;
    private boolean done;

    private MessageDigestHasher(MessageDigest p, int q) {
      this.digest = p;
      this.bytes = q;
    }

    @Override
    protected void a(byte b) {
      b();
      digest.update(b);
    }

    @Override
    protected void a(byte[] b, int r, int s) {
      b();
      digest.update(b, r, s);
    }

    @Override
    protected void a(ByteBuffer t) {
      b();
      digest.update(t);
    }

    private void b() {
      checkState(!done, "Cannot re-use a Hasher after calling hash() on it");
    }

    @Override
    public HashCode c() {
      b();
      done = true;
      return (bytes == digest.getDigestLength())
          ? HashCode.fromBytesNoCopy(digest.digest())
          : HashCode.fromBytesNoCopy(Arrays.copyOf(digest.digest(), bytes));
    }
  }
}
