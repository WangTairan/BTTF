package org.bukkit.util.noise;
import java.util.Random;
import org.bukkit.World;

/* loaded from: SimplexNoiseGenerator.class */
public class SimplexNoiseGenerator extends PerlinNoiseGenerator {
    protected static final double F3 = 0.3333333333333333d;
    protected static final double G3 = 0.16666666666666666d;
    protected static double offsetW;
    protected static final double SQRT_3 = Math.sqrt(3.0d);
    protected static final double SQRT_5 = Math.sqrt(5.0d);
    protected static final double F2 = 0.5d * (SQRT_3 - 1.0d);
    protected static final double G2 = (3.0d - SQRT_3) / 6.0d;
    protected static final double G22 = (G2 * 2.0d) - 1.0d;
    protected static final double F4 = (SQRT_5 - 1.0d) / 4.0d;
    protected static final double G4 = (5.0d - SQRT_5) / 20.0d;
    protected static final double G42 = G4 * 2.0d;
    protected static final double G43 = G4 * 3.0d;
    protected static final double G44 = (G4 * 4.0d) - 1.0d;
    protected static final int[][] grad4 = {new int[]{0, 1, 1, 1}, new int[]{0, 1, 1, -1}, new int[]{0, 1, -1, 1}, new int[]{0, 1, -1, -1}, new int[]{0, -1, 1, 1}, new int[]{0, -1, 1, -1}, new int[]{0, -1, -1, 1}, new int[]{0, -1, -1, -1}, new int[]{1, 0, 1, 1}, new int[]{1, 0, 1, -1}, new int[]{1, 0, -1, 1}, new int[]{1, 0, -1, -1}, new int[]{-1, 0, 1, 1}, new int[]{-1, 0, 1, -1}, new int[]{-1, 0, -1, 1}, new int[]{-1, 0, -1, -1}, new int[]{1, 1, 0, 1}, new int[]{1, 1, 0, -1}, new int[]{1, -1, 0, 1}, new int[]{1, -1, 0, -1}, new int[]{-1, 1, 0, 1}, new int[]{-1, 1, 0, -1}, new int[]{-1, -1, 0, 1}, new int[]{-1, -1, 0, -1}, new int[]{1, 1, 1, 0}, new int[]{1, 1, -1, 0}, new int[]{1, -1, 1, 0}, new int[]{1, -1, -1, 0}, new int[]{-1, 1, 1, 0}, new int[]{-1, 1, -1, 0}, new int[]{-1, -1, 1, 0}, new int[]{-1, -1, -1, 0}};
    protected static final int[][] simplex = {new int[]{0, 1, 2, 3}, new int[]{0, 1, 3, 2}, new int[]{0, 0, 0, 0}, new int[]{0, 2, 3, 1}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{1, 2, 3, 0}, new int[]{0, 2, 1, 3}, new int[]{0, 0, 0, 0}, new int[]{0, 3, 1, 2}, new int[]{0, 3, 2, 1}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{1, 3, 2, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{1, 2, 0, 3}, new int[]{0, 0, 0, 0}, new int[]{1, 3, 0, 2}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{2, 3, 0, 1}, new int[]{2, 3, 1, 0}, new int[]{1, 0, 2, 3}, new int[]{1, 0, 3, 2}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{2, 0, 3, 1}, new int[]{0, 0, 0, 0}, new int[]{2, 1, 3, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{2, 0, 1, 3}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{3, 0, 1, 2}, new int[]{3, 0, 2, 1}, new int[]{0, 0, 0, 0}, new int[]{3, 1, 2, 0}, new int[]{2, 1, 0, 3}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{0, 0, 0, 0}, new int[]{3, 1, 0, 2}, new int[]{0, 0, 0, 0}, new int[]{3, 2, 0, 1}, new int[]{3, 2, 1, 0}};
    private static final SimplexNoiseGenerator instance = new SimplexNoiseGenerator();

    protected SimplexNoiseGenerator() {
    }

    public SimplexNoiseGenerator(World world) {
        this(new Random(world.getSeed()));
    }

    public SimplexNoiseGenerator(long seed) {
        this(new Random(seed));
    }

    public SimplexNoiseGenerator(Random rand) {
        super(rand);
        offsetW = rand.nextDouble() * 256.0d;
    }

    protected static double dot(int[] g, double x, double y) {
        return (g[0] * x) + (g[1] * y);
    }

    protected static double dot(int[] g, double x, double y, double z) {
        return (g[0] * x) + (g[1] * y) + (g[2] * z);
    }

    protected static double dot(int[] g, double x, double y, double z, double w) {
        return (g[0] * x) + (g[1] * y) + (g[2] * z) + (g[3] * w);
    }

    public static double getNoise(double xin) {
        return instance.noise(xin);
    }

    public static double getNoise(double xin, double yin) {
        return instance.noise(xin, yin);
    }

    public static double getNoise(double xin, double yin, double zin) {
        return instance.noise(xin, yin, zin);
    }

    public static double getNoise(double x, double y, double z, double w) {
        return instance.noise(x, y, z, w);
    }

    @Override // org.bukkit.util.noise.PerlinNoiseGenerator, org.bukkit.util.noise.NoiseGenerator
    public double noise(double xin, double yin, double zin) {
        int i1;
        int j1;
        int k1;
        int i2;
        int j2;
        int k2;
        double n0;
        double n1;
        double n2;
        double n3;
        double xin2 = xin + this.offsetX;
        double yin2 = yin + this.offsetY;
        double zin2 = zin + this.offsetZ;
        double s = (xin2 + yin2 + zin2) * F3;
        int i = floor(xin2 + s);
        int j = floor(yin2 + s);
        int k = floor(zin2 + s);
        double t = (i + j + k) * G3;
        double X0 = i - t;
        double Y0 = j - t;
        double Z0 = k - t;
        double x0 = xin2 - X0;
        double y0 = yin2 - Y0;
        double z0 = zin2 - Z0;
        if (x0 >= y0) {
            if (y0 >= z0) {
                i1 = 1;
                j1 = 0;
                k1 = 0;
                i2 = 1;
                j2 = 1;
                k2 = 0;
            } else if (x0 >= z0) {
                i1 = 1;
                j1 = 0;
                k1 = 0;
                i2 = 1;
                j2 = 0;
                k2 = 1;
            } else {
                i1 = 0;
                j1 = 0;
                k1 = 1;
                i2 = 1;
                j2 = 0;
                k2 = 1;
            }
        } else if (y0 < z0) {
            i1 = 0;
            j1 = 0;
            k1 = 1;
            i2 = 0;
            j2 = 1;
            k2 = 1;
        } else if (x0 < z0) {
            i1 = 0;
            j1 = 1;
            k1 = 0;
            i2 = 0;
            j2 = 1;
            k2 = 1;
        } else {
            i1 = 0;
            j1 = 1;
            k1 = 0;
            i2 = 1;
            j2 = 1;
            k2 = 0;
        }
        double x1 = (x0 - i1) + G3;
        double y1 = (y0 - j1) + G3;
        double z1 = (z0 - k1) + G3;
        double x2 = (x0 - i2) + F3;
        double y2 = (y0 - j2) + F3;
        double z2 = (z0 - k2) + F3;
        double x3 = (x0 - 1.0d) + 0.5d;
        double y3 = (y0 - 1.0d) + 0.5d;
        double z3 = (z0 - 1.0d) + 0.5d;
        int ii = i & 255;
        int jj = j & 255;
        int kk = k & 255;
        int gi0 = this.perm[ii + this.perm[jj + this.perm[kk]]] % 12;
        int gi1 = this.perm[(ii + i1) + this.perm[(jj + j1) + this.perm[kk + k1]]] % 12;
        int gi2 = this.perm[(ii + i2) + this.perm[(jj + j2) + this.perm[kk + k2]]] % 12;
        int gi3 = this.perm[(ii + 1) + this.perm[(jj + 1) + this.perm[kk + 1]]] % 12;
        double t0 = ((0.6d - (x0 * x0)) - (y0 * y0)) - (z0 * z0);
        if (t0 < 0.0d) {
            n0 = 0.0d;
        } else {
            double t02 = t0 * t0;
            n0 = t02 * t02 * dot(grad3[gi0], x0, y0, z0);
        }
        double t1 = ((0.6d - (x1 * x1)) - (y1 * y1)) - (z1 * z1);
        if (t1 < 0.0d) {
            n1 = 0.0d;
        } else {
            double t12 = t1 * t1;
            n1 = t12 * t12 * dot(grad3[gi1], x1, y1, z1);
        }
        double t2 = ((0.6d - (x2 * x2)) - (y2 * y2)) - (z2 * z2);
        if (t2 < 0.0d) {
            n2 = 0.0d;
        } else {
            double t22 = t2 * t2;
            n2 = t22 * t22 * dot(grad3[gi2], x2, y2, z2);
        }
        double t3 = ((0.6d - (x3 * x3)) - (y3 * y3)) - (z3 * z3);
        if (t3 < 0.0d) {
            n3 = 0.0d;
        } else {
            double t32 = t3 * t3;
            n3 = t32 * t32 * dot(grad3[gi3], x3, y3, z3);
        }
        return 32.0d * (n0 + n1 + n2 + n3);
    }

    @Override // org.bukkit.util.noise.NoiseGenerator
    public double noise(double xin, double yin) {
        int i1;
        int j1;
        double n0;
        double n1;
        double n2;
        double xin2 = xin + this.offsetX;
        double yin2 = yin + this.offsetY;
        double s = (xin2 + yin2) * F2;
        int i = floor(xin2 + s);
        int j = floor(yin2 + s);
        double t = (i + j) * G2;
        double X0 = i - t;
        double Y0 = j - t;
        double x0 = xin2 - X0;
        double y0 = yin2 - Y0;
        if (x0 > y0) {
            i1 = 1;
            j1 = 0;
        } else {
            i1 = 0;
            j1 = 1;
        }
        double x1 = (x0 - i1) + G2;
        double y1 = (y0 - j1) + G2;
        double x2 = x0 + G22;
        double y2 = y0 + G22;
        int ii = i & 255;
        int jj = j & 255;
        int gi0 = this.perm[ii + this.perm[jj]] % 12;
        int gi1 = this.perm[(ii + i1) + this.perm[jj + j1]] % 12;
        int gi2 = this.perm[(ii + 1) + this.perm[jj + 1]] % 12;
        double t0 = (0.5d - (x0 * x0)) - (y0 * y0);
        if (t0 < 0.0d) {
            n0 = 0.0d;
        } else {
            double t02 = t0 * t0;
            n0 = t02 * t02 * dot(grad3[gi0], x0, y0);
        }
        double t1 = (0.5d - (x1 * x1)) - (y1 * y1);
        if (t1 < 0.0d) {
            n1 = 0.0d;
        } else {
            double t12 = t1 * t1;
            n1 = t12 * t12 * dot(grad3[gi1], x1, y1);
        }
        double t2 = (0.5d - (x2 * x2)) - (y2 * y2);
        if (t2 < 0.0d) {
            n2 = 0.0d;
        } else {
            double t22 = t2 * t2;
            n2 = t22 * t22 * dot(grad3[gi2], x2, y2);
        }
        return 70.0d * (n0 + n1 + n2);
    }

    public double noise(double x, double y, double z, double w) {
        double n0;
        double n1;
        double n2;
        double n3;
        double n4;
        double x2 = x + this.offsetX;
        double y2 = y + this.offsetY;
        double z2 = z + this.offsetZ;
        double w2 = w + offsetW;
        double s = (x2 + y2 + z2 + w2) * F4;
        int i = floor(x2 + s);
        int j = floor(y2 + s);
        int k = floor(z2 + s);
        int l = floor(w2 + s);
        double t = (i + j + k + l) * G4;
        double X0 = i - t;
        double Y0 = j - t;
        double Z0 = k - t;
        double W0 = l - t;
        double x0 = x2 - X0;
        double y0 = y2 - Y0;
        double z0 = z2 - Z0;
        double w0 = w2 - W0;
        int c1 = x0 > y0 ? 32 : 0;
        int c2 = x0 > z0 ? 16 : 0;
        int c3 = y0 > z0 ? 8 : 0;
        int c4 = x0 > w0 ? 4 : 0;
        int c5 = y0 > w0 ? 2 : 0;
        int c6 = z0 > w0 ? 1 : 0;
        int c = c1 + c2 + c3 + c4 + c5 + c6;
        int i1 = simplex[c][0] >= 3 ? 1 : 0;
        int j1 = simplex[c][1] >= 3 ? 1 : 0;
        int k1 = simplex[c][2] >= 3 ? 1 : 0;
        int l1 = simplex[c][3] >= 3 ? 1 : 0;
        int i2 = simplex[c][0] >= 2 ? 1 : 0;
        int j2 = simplex[c][1] >= 2 ? 1 : 0;
        int k2 = simplex[c][2] >= 2 ? 1 : 0;
        int l2 = simplex[c][3] >= 2 ? 1 : 0;
        int i3 = simplex[c][0] >= 1 ? 1 : 0;
        int j3 = simplex[c][1] >= 1 ? 1 : 0;
        int k3 = simplex[c][2] >= 1 ? 1 : 0;
        int l3 = simplex[c][3] >= 1 ? 1 : 0;
        double x1 = (x0 - i1) + G4;
        double y1 = (y0 - j1) + G4;
        double z1 = (z0 - k1) + G4;
        double w1 = (w0 - l1) + G4;
        double x22 = (x0 - i2) + G42;
        double y22 = (y0 - j2) + G42;
        double z22 = (z0 - k2) + G42;
        double w22 = (w0 - l2) + G42;
        double x3 = (x0 - i3) + G43;
        double y3 = (y0 - j3) + G43;
        double z3 = (z0 - k3) + G43;
        double w3 = (w0 - l3) + G43;
        double x4 = x0 + G44;
        double y4 = y0 + G44;
        double z4 = z0 + G44;
        double w4 = w0 + G44;
        int ii = i & 255;
        int jj = j & 255;
        int kk = k & 255;
        int ll = l & 255;
        int gi0 = this.perm[ii + this.perm[jj + this.perm[kk + this.perm[ll]]]] % 32;
        int gi1 = this.perm[(ii + i1) + this.perm[(jj + j1) + this.perm[(kk + k1) + this.perm[ll + l1]]]] % 32;
        int gi2 = this.perm[(ii + i2) + this.perm[(jj + j2) + this.perm[(kk + k2) + this.perm[ll + l2]]]] % 32;
        int gi3 = this.perm[(ii + i3) + this.perm[(jj + j3) + this.perm[(kk + k3) + this.perm[ll + l3]]]] % 32;
        int gi4 = this.perm[(ii + 1) + this.perm[(jj + 1) + this.perm[(kk + 1) + this.perm[ll + 1]]]] % 32;
        double t0 = (((0.6d - (x0 * x0)) - (y0 * y0)) - (z0 * z0)) - (w0 * w0);
        if (t0 < 0.0d) {
            n0 = 0.0d;
        } else {
            double t02 = t0 * t0;
            n0 = t02 * t02 * dot(grad4[gi0], x0, y0, z0, w0);
        }
        double t1 = (((0.6d - (x1 * x1)) - (y1 * y1)) - (z1 * z1)) - (w1 * w1);
        if (t1 < 0.0d) {
            n1 = 0.0d;
        } else {
            double t12 = t1 * t1;
            n1 = t12 * t12 * dot(grad4[gi1], x1, y1, z1, w1);
        }
        double t2 = (((0.6d - (x22 * x22)) - (y22 * y22)) - (z22 * z22)) - (w22 * w22);
        if (t2 < 0.0d) {
            n2 = 0.0d;
        } else {
            double t22 = t2 * t2;
            n2 = t22 * t22 * dot(grad4[gi2], x22, y22, z22, w22);
        }
        double t3 = (((0.6d - (x3 * x3)) - (y3 * y3)) - (z3 * z3)) - (w3 * w3);
        if (t3 < 0.0d) {
            n3 = 0.0d;
        } else {
            double t32 = t3 * t3;
            n3 = t32 * t32 * dot(grad4[gi3], x3, y3, z3, w3);
        }
        double t4 = (((0.6d - (x4 * x4)) - (y4 * y4)) - (z4 * z4)) - (w4 * w4);
        if (t4 < 0.0d) {
            n4 = 0.0d;
        } else {
            double t42 = t4 * t4;
            n4 = t42 * t42 * dot(grad4[gi4], x4, y4, z4, w4);
        }
        return 27.0d * (n0 + n1 + n2 + n3 + n4);
    }

    public static SimplexNoiseGenerator getInstance() {
        return instance;
    }
}
