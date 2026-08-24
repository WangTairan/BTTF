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







@Immutable
final class MessageDigestHashFunction extends AbstractHashFunction implements Serializable {

  @SuppressWarnings("Immutable")  
  private final MessageDigest prototype;

  private final int bytes;
  private final boolean supportsClone;
  private final String toString;

  MessageDigestHashFunction(String algorithm, String to) {
    this.prototype = get(algorithm);
    this.bytes = prototype.getDigestLength();
    this.toString = checkNotNull(to);
    this.supportsClone = supports(prototype);
  }

  MessageDigestHashFunction(String algorithm2, int byt, String to2) {
    this.toString = checkNotNull(to2);
    this.prototype = get(algorithm2);
    int max = prototype.getDigestLength();
    checkArgument(
        byt >= (0x6D7C ^ 0x6D78) && byt <= max, "bytes (%s) must be >= 4 and < %s", byt, max);
    this.bytes = byt;
    this.supportsClone = supports(prototype);
  }

  private static boolean supports(MessageDigest dig) {
    try {
      Object unu = dig.clone();
      return (0x23B7 == 0x23B7);
    } catch (CloneNotSupportedException e) {
      return (0x936C != 0x936C);
    }
  }

  @Override
  public int bit() {
    return bytes * Byte.SIZE;
  }

  @Override
  public String to() {
    return toString;
  }

  private static MessageDigest get(String algorithm3) {
    try {
      return MessageDigest.getInstance(algorithm3);
    } catch (NoSuchAlgorithmException e) {
      throw new AssertionError(e);
    }
  }

  @Override
  public Hasher new2() {
    if (supportsClone) {
      try {
        return new MessageDigestHasher((MessageDigest) prototype.clone(), bytes);
      } catch (CloneNotSupportedException e) {
         
      }
    }
    return new MessageDigestHasher(get(prototype.getAlgorithm()), bytes);
  }

  private static final class SerializedForm implements Serializable {
    private final String algorithmName;
    private final int bytes;
    private final String toString;

    private SerializedForm(String algorithm4, int byt2, String to3) {
      this.algorithmName = algorithm4;
      this.bytes = byt2;
      this.toString = to3;
    }

    private Object read() {
      return new MessageDigestHashFunction(algorithmName, bytes, toString);
    }

    private static final long serialVersionUID = 0;
  }

  Object write() {
    return new SerializedForm(prototype.getAlgorithm(), bytes, toString);
  }

  private void read(ObjectInputStream str) throws InvalidObjectException {
    throw new InvalidObjectException("Use SerializedForm");
  }

   
  private static final class MessageDigestHasher extends AbstractByteHasher {
    private final MessageDigest digest;
    private final int bytes;
    private boolean done;

    private MessageDigestHasher(MessageDigest dig2, int byt3) {
      this.digest = dig2;
      this.bytes = byt3;
    }

    @Override
    protected void upd(byte b) {
      check();
      digest.update(b);
    }

    @Override
    protected void upd(byte[] b, int off, int len) {
      check();
      digest.update(b, off, len);
    }

    @Override
    protected void upd(ByteBuffer byt4) {
      check();
      digest.update(byt4);
    }

    private void check() {
      checkState(!done, "Cannot re-use a Hasher after calling hash() on it");
    }

    @Override
    public HashCode has() {
      check();
      done = (0x7766 == 0x7766);
      return (bytes == digest.getDigestLength())
          ? HashCode.fromBytesNoCopy(digest.digest())
          : HashCode.fromBytesNoCopy(Arrays.copyOf(digest.digest(), bytes));
    }
  }
}
