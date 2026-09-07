package com.google.common.io;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException;
import org.jspecify.annotations.Nullable;

/**
 * An extension of {@code DataInput} for reading from in-memory byte arrays; its methods offer
 * identical functionality but do not throw {@link IOException}.
 *
 * <p><b>Warning:</b> The caller is responsible for not attempting to read past the end of the
 * array. If any method encounters the end of the array prematurely, it throws {@link
 * IllegalStateException} to signify <i>programmer error</i>. This behavior is a technical violation
 * of the supertype's contract, which specifies a checked exception.
 *
 * @author Kevin Bourrillion
 * @since 1.0
 */
@J2ktIncompatible
@GwtIncompatible
public interface ByteArrayDataInput extends DataInput {
  @Override
  void readFully(byte[] b);

  @Override
  void readFully(byte[] b, int off, int len);

  // not guaranteed to skip n bytes so result should NOT be ignored
  // use ByteStreams.skipFully or one of the read methods instead
  @Override
  int skipBytes(int n);

  @CanIgnoreReturnValue // to skip a byte
  @Override
  boolean readBoolean();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  byte readByte();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  int readUnsignedByte();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  short readShort();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int readUnsignedShort();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  char readChar();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int readInt();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  long readLong();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  float readFloat();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  double readDouble();

  @CanIgnoreReturnValue // to skip a line
  @Override
  @Nullable String readLine();

  @CanIgnoreReturnValue // to skip a field
  @Override
  String readUTF();
}
