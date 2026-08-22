package org.apache.commons.imaging.formats.pnm;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Map;
import org.apache.commons.imaging.ImageWriteException;

/* loaded from: PpmWriter.class */
class PpmWriter extends PnmWriter {
    public PpmWriter(boolean rawbits) {
        super(rawbits);
    }

    @Override // org.apache.commons.imaging.formats.pnm.PnmWriter
    public void writeImage(BufferedImage src, OutputStream os, Map<String, Object> params) throws ImageWriteException, IOException {
        os.write(80);
        os.write(this.rawbits ? 54 : 51);
        os.write(32);
        int width = src.getWidth();
        int height = src.getHeight();
        os.write(Integer.toString(width).getBytes("US-ASCII"));
        os.write(32);
        os.write(Integer.toString(height).getBytes("US-ASCII"));
        os.write(32);
        os.write(Integer.toString(255).getBytes("US-ASCII"));
        os.write(10);
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int argb = src.getRGB(x, y);
                int red = 255 & (argb >> 16);
                int green = 255 & (argb >> 8);
                int blue = 255 & (argb >> 0);
                if (this.rawbits) {
                    os.write((byte) red);
                    os.write((byte) green);
                    os.write((byte) blue);
                } else {
                    os.write(Integer.toString(red).getBytes("US-ASCII"));
                    os.write(32);
                    os.write(Integer.toString(green).getBytes("US-ASCII"));
                    os.write(32);
                    os.write(Integer.toString(blue).getBytes("US-ASCII"));
                    os.write(32);
                }
            }
        }
    }
}
