package org.apache.commons.imaging.formats.png;
import java.util.Arrays;

/*
 * This class specifies class file version 49.0 but uses Java 6 signatures.  Assumed Java 6.
 */
public enum ColorType {
    GREYSCALE(0, true, false, 1, new int[]{1, 2, 4, 8, 16}),
    TRUE_COLOR(2, false, false, 3, new int[]{8, 16}),
    INDEXED_COLOR(3, false, false, 1, new int[]{1, 2, 4, 8}),
    GREYSCALE_WITH_ALPHA(4, true, true, 2, new int[]{8, 16}),
    TRUE_COLOR_WITH_ALPHA(6, false, true, 4, new int[]{8, 16});

    private final int value;
    private final boolean greyscale;
    private final boolean alpha;
    private final int samplesPerPixel;
    private final int[] allowedBitDepths;

    private ColorType(int value, boolean greyscale, boolean alpha, int samplesPerPixel, int[] allowedBitDepths) {
        this.value = value;
        this.greyscale = greyscale;
        this.alpha = alpha;
        this.samplesPerPixel = samplesPerPixel;
        this.allowedBitDepths = allowedBitDepths;
    }

    int getValue() {
        return this.value;
    }

    boolean isGreyscale() {
        return this.greyscale;
    }

    boolean hasAlpha() {
        return this.alpha;
    }

    int getSamplesPerPixel() {
        return this.samplesPerPixel;
    }

    boolean isBitDepthAllowed(int bitDepth) {
        return Arrays.binarySearch(this.allowedBitDepths, bitDepth) >= 0;
    }

    public static ColorType getColorType(int value) {
        for (ColorType type : ColorType.values()) {
            if (type.value != value) continue;
            return type;
        }
        return null;
    }

    static ColorType getColorType(boolean alpha, boolean grayscale) {
        if (grayscale) {
            if (alpha) {
                return GREYSCALE_WITH_ALPHA;
            }
            return GREYSCALE;
        }
        if (alpha) {
            return TRUE_COLOR_WITH_ALPHA;
        }
        return TRUE_COLOR;
    }
}
