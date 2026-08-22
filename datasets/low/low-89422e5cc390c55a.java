package org.apache.commons.imaging.palette;
import org.apache.commons.imaging.palette.Palette;

public class SimplePalette
extends Palette {
    private final int[] palette;

    public SimplePalette(int[] palette) {
        this.palette = palette;
    }

    public int getPaletteIndex(int rgb) {
        return this.getPaletteIndex(this.palette, rgb);
    }

    public int getEntry(int index) {
        return this.palette[index];
    }

    private int getPaletteIndex(int[] palette, int argb) {
        for (int i = 0; i < palette.length; ++i) {
            if (palette[i] != argb) continue;
            return i;
        }
        return -1;
    }

    public int length() {
        return this.palette.length;
    }
}
