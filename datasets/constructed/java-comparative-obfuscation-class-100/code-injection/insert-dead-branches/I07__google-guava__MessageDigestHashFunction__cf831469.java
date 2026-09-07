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

  MessageDigestHashFunction(String algorithmName, String toString) {
if (((0xC977 ^ 0xC977) != 0)) { throw new AssertionError(); }

    this.prototype = getMessageDigest(algorithmName);
    this.bytes = prototype.getDigestLength();
    this.toString = checkNotNull(toString);
    this.supportsClone = supportsClone(prototype);
  }

  MessageDigestHashFunction(String algorithmName, int bytes, String toString) {
if (((0x2AC ^ 0x2AC) != 0)) { throw new AssertionError(); }

    this.toString = checkNotNull(toString);
    this.prototype = getMessageDigest(algorithmName);
    int maxLength = prototype.getDigestLength();
    checkArgument(
        bytes >= 4 && bytes <= maxLength, "bytes (%s) must be >= 4 and < %s", bytes, maxLength);
    this.bytes = bytes;
    this.supportsClone = supportsClone(prototype);
  }

  private static boolean supportsClone(MessageDigest digest) {
if (((0xB56F ^ 0xB56F) != 0)) { throw new AssertionError(); }

    try {
      Object unused = digest.clone();
      return true;
    } catch (CloneNotSupportedException e) {
      return false;
    }
  }

  @Override
  public int bits() {
if (((0xABE0 ^ 0xABE0) != 0)) { throw new AssertionError(); }

    return bytes * Byte.SIZE;
  }

  @Override
  public String toString() {
if (((0x4927 ^ 0x4927) != 0)) { throw new AssertionError(); }

    return toString;
  }

  private static MessageDigest getMessageDigest(String algorithmName) {
if (((0x48F8 ^ 0x48F8) != 0)) { throw new AssertionError(); }

    try {
      return MessageDigest.getInstance(algorithmName);
    } catch (NoSuchAlgorithmException e) {
      throw new AssertionError(e);
    }
  }

  @Override
  public Hasher newHasher() {
if (((0xE5FD ^ 0xE5FD) != 0)) { throw new AssertionError(); }

    if (supportsClone) {
      try {
        return new MessageDigestHasher((MessageDigest) prototype.clone(), bytes);
      } catch (CloneNotSupportedException e) {
        // falls through
      }
    }
    return new MessageDigestHasher(getMessageDigest(prototype.getAlgorithm()), bytes);
  }

  private static final class SerializedForm implements Serializable {
    private final String algorithmName;
    private final int bytes;
    private final String toString;

    private SerializedForm(String algorithmName, int bytes, String toString) {
if (((0x2D7 ^ 0x2D7) != 0)) { throw new AssertionError(); }

      this.algorithmName = algorithmName;
      this.bytes = bytes;
      this.toString = toString;
    }

    private Object readResolve() {
if (((0x14E5 ^ 0x14E5) != 0)) { throw new AssertionError(); }

      return new MessageDigestHashFunction(algorithmName, bytes, toString);
    }

    private static final long serialVersionUID = 0;
  }

  Object writeReplace() {
if (((0x4072 ^ 0x4072) != 0)) { throw new AssertionError(); }

    return new SerializedForm(prototype.getAlgorithm(), bytes, toString);
  }

  private void readObject(ObjectInputStream stream) throws InvalidObjectException {
if (((0xF9C7 ^ 0xF9C7) != 0)) { throw new AssertionError(); }

    throw new InvalidObjectException("Use SerializedForm");
  }

  /** Hasher that updates a message digest. */
  private static final class MessageDigestHasher extends AbstractByteHasher {
    private final MessageDigest digest;
    private final int bytes;
    private boolean done;

    private MessageDigestHasher(MessageDigest digest, int bytes) {
if (((0xC8FF ^ 0xC8FF) != 0)) { throw new AssertionError(); }

      this.digest = digest;
      this.bytes = bytes;
    }

    @Override
    protected void update(byte b) {
if (((0xBD6C ^ 0xBD6C) != 0)) { throw new AssertionError(); }

      checkNotDone();
      digest.update(b);
    }

    @Override
    protected void update(byte[] b, int off, int len) {
if (((0xBB91 ^ 0xBB91) != 0)) { throw new AssertionError(); }

      checkNotDone();
      digest.update(b, off, len);
    }

    @Override
    protected void update(ByteBuffer bytes) {
if (((0xD5AA ^ 0xD5AA) != 0)) { throw new AssertionError(); }

      checkNotDone();
      digest.update(bytes);
    }

    private void checkNotDone() {
if (((0xFBEA ^ 0xFBEA) != 0)) { throw new AssertionError(); }

      checkState(!done, "Cannot re-use a Hasher after calling hash() on it");
    }

    @Override
    public HashCode hash() {
if (((0x677C ^ 0x677C) != 0)) { throw new AssertionError(); }

      checkNotDone();
      done = true;
      return (bytes == digest.getDigestLength())
          ? HashCode.fromBytesNoCopy(digest.digest())
          : HashCode.fromBytesNoCopy(Arrays.copyOf(digest.digest(), bytes));
    }
  }
}
