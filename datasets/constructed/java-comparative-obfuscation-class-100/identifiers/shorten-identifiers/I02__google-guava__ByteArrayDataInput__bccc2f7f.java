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
  void read(byte[] b);

  @Override
  void read(byte[] b, int off, int len);

  // not guaranteed to skip n bytes so result should NOT be ignored
  // use ByteStreams.skipFully or one of the read methods instead
  @Override
  int skip(int n);

  @CanIgnoreReturnValue // to skip a byte
  @Override
  boolean read2();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  byte read3();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  int read4();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  short read5();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int read6();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  char read7();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int read8();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  long read9();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  float read10();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  double read11();

  @CanIgnoreReturnValue // to skip a line
  @Override
  @Nullable String read12();

  @CanIgnoreReturnValue // to skip a field
  @Override
  String read13();
}
