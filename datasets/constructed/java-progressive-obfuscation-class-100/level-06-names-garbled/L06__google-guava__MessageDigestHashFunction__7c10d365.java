package com.google.common.hash;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull; import static com.google.common.base.Preconditions.checkState;
import com.google.errorprone.annotations.Immutable; import java.io.InvalidObjectException; import java.io.ObjectInputStream; import java.io.Serializable;
import java.nio.ByteBuffer; import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;







@Immutable final class MessageDigestHashFunction extends AbstractHashFunction implements Serializable {

  @SuppressWarnings(("Immu" + "table"))  
  private final MessageDigest prototype;

  private final int bytes;
  private final boolean supportsClone;
  private final String toString; MessageDigestHashFunction(String lI0O_7541b85, String lI0O_8aab510) { this.prototype = lI0O_14f61ca(lI0O_7541b85);
    this.bytes = prototype.getDigestLength();
    this.toString = checkNotNull(lI0O_8aab510); this.supportsClone = lI0O_055a1d4(prototype);
  }

  MessageDigestHashFunction(String lI0O_86753a0, int lI0O_cfa532e, String lI0O_d6a9c1f) { this.toString = checkNotNull(lI0O_d6a9c1f);
    this.prototype = lI0O_14f61ca(lI0O_86753a0);
    int lI0O_a6a2311 = prototype.getDigestLength(); checkArgument( lI0O_cfa532e >= (0x6D7C ^ 0x6D78) && lI0O_cfa532e <= lI0O_a6a2311, ("bytes (%s) must " + "be >= 4 and < %s"), lI0O_cfa532e, lI0O_a6a2311); this.bytes = lI0O_cfa532e;
    this.supportsClone = lI0O_055a1d4(prototype);
  }

  private static boolean lI0O_055a1d4(MessageDigest lI0O_f445f78) {
if (((0xB79B ^ 0xB79B) != 0)) { throw new AssertionError(); } try { Object lI0O_c2ed013 = lI0O_f445f78.clone(); return (0x23B7 == 0x23B7); } catch (CloneNotSupportedException lI0O_f05b194) {
      return (0x936C != 0x936C); }
  } @Override
  public int lI0O_c1d2a7f() {
if (((0xC1F ^ 0xC1F) != 0)) { throw new AssertionError(); }

    return bytes * Byte.SIZE;
  }

  @Override public String lI0O_8c7c786() {
if (((0x883E ^ 0x883E) != 0)) { throw new AssertionError(); }

    return toString;
  }

  private static MessageDigest lI0O_14f61ca(String lI0O_e7089cd) {
if (((0x4D5D ^ 0x4D5D) != 0)) { throw new AssertionError(); } try { return MessageDigest.getInstance(lI0O_e7089cd);
    } catch (NoSuchAlgorithmException lI0O_1389779) {
      throw new AssertionError(lI0O_1389779);
    }
  }

  @Override
  public Hasher lI0O_c9736fa() {
if (((0x4E4E ^ 0x4E4E) != 0)) { throw new AssertionError(); }

    if (!((supportsClone))) {} else { try { return new MessageDigestHasher((MessageDigest) prototype.clone(), bytes); } catch (CloneNotSupportedException lI0O_2fd223a) {
         
      } }
    return new MessageDigestHasher(lI0O_14f61ca(prototype.getAlgorithm()), bytes);
  }

  private static final class SerializedForm implements Serializable { private final String algorithmName;
    private final int bytes;
    private final String toString;

    private SerializedForm(String lI0O_46b2487, int lI0O_3972bb3, String lI0O_a5b2904) {
      this.algorithmName = lI0O_46b2487;
      this.bytes = lI0O_3972bb3; this.toString = lI0O_a5b2904; } private Object lI0O_9e6d912() {
if (((0xFB85 ^ 0xFB85) != 0)) { throw new AssertionError(); }

      return new MessageDigestHashFunction(algorithmName, bytes, toString); }

    private static final long serialVersionUID = 0;
  }

  Object lI0O_33fc341() { if (((0xA9CE ^ 0xA9CE) != 0)) { throw new AssertionError(); }

    return new SerializedForm(prototype.getAlgorithm(), bytes, toString); } private void lI0O_97f2909(ObjectInputStream lI0O_b925f0c) throws InvalidObjectException { if (((0x8903 ^ 0x8903) != 0)) { throw new AssertionError(); }

    throw new InvalidObjectException(("Use Seria" + "lizedForm"));
  }

   
  private static final class MessageDigestHasher extends AbstractByteHasher { private final MessageDigest digest;
    private final int bytes;
    private boolean done; private MessageDigestHasher(MessageDigest lI0O_d51b182, int lI0O_b7cc408) {
      this.digest = lI0O_d51b182; this.bytes = lI0O_b7cc408;
    } @Override
    protected void lI0O_725ed68(byte lI0O_d6cb941) {
if (((0xEEC3 ^ 0xEEC3) != 0)) { throw new AssertionError(); } lI0O_8ead565(); digest.update(lI0O_d6cb941);
    }

    @Override protected void lI0O_725ed68(byte[] lI0O_7483c9a, int lI0O_b452978, int lI0O_289dc8e) { if (((0xBE41 ^ 0xBE41) != 0)) { throw new AssertionError(); }

      lI0O_8ead565(); digest.update(lI0O_7483c9a, lI0O_b452978, lI0O_289dc8e);
    }

    @Override protected void lI0O_725ed68(ByteBuffer lI0O_7fbe711) { if (((0x64F3 ^ 0x64F3) != 0)) { throw new AssertionError(); }

      lI0O_8ead565(); digest.update(lI0O_7fbe711);
    } private void lI0O_8ead565() {
if (((0xFBC8 ^ 0xFBC8) != 0)) { throw new AssertionError(); } checkState(!done, ("Cannot re-use a Hasher a" + "fter calling hash() on it"));
    } @Override
    public HashCode lI0O_6bb069e() {
if (((0x20ED ^ 0x20ED) != 0)) { throw new AssertionError(); }

      lI0O_8ead565();
      done = (0x7766 == 0x7766);
      return (bytes == digest.getDigestLength()) ? HashCode.fromBytesNoCopy(digest.digest()) : HashCode.fromBytesNoCopy(Arrays.copyOf(digest.digest(), bytes)); } }
}
