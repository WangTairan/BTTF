package org.bukkit;
import org.bukkit.block.Block;
import org.bukkit.util.NumberConversions;
import org.bukkit.util.Vector;

/* loaded from: Location.class */
public class Location implements Cloneable {
    private World world;
    private double x;
    private double y;
    private double z;
    private float pitch;
    private float yaw;

    public Location(World world, double x, double y, double z) {
        this(world, x, y, z, 0.0f, 0.0f);
    }

    public Location(World world, double x, double y, double z, float yaw, float pitch) {
        this.world = world;
        this.x = x;
        this.y = y;
        this.z = z;
        this.pitch = pitch;
        this.yaw = yaw;
    }

    public void setWorld(World world) {
        this.world = world;
    }

    public World getWorld() {
        return this.world;
    }

    public Chunk getChunk() {
        return this.world.getChunkAt(this);
    }

    public Block getBlock() {
        return this.world.getBlockAt(this);
    }

    public void setX(double x) {
        this.x = x;
    }

    public double getX() {
        return this.x;
    }

    public int getBlockX() {
        return locToBlock(this.x);
    }

    public void setY(double y) {
        this.y = y;
    }

    public double getY() {
        return this.y;
    }

    public int getBlockY() {
        return locToBlock(this.y);
    }

    public void setZ(double z) {
        this.z = z;
    }

    public double getZ() {
        return this.z;
    }

    public int getBlockZ() {
        return locToBlock(this.z);
    }

    public void setYaw(float yaw) {
        this.yaw = yaw;
    }

    public float getYaw() {
        return this.yaw;
    }

    public void setPitch(float pitch) {
        this.pitch = pitch;
    }

    public float getPitch() {
        return this.pitch;
    }

    public Vector getDirection() {
        Vector vector = new Vector();
        double rotX = getYaw();
        double rotY = getPitch();
        vector.setY(-Math.sin(Math.toRadians(rotY)));
        double xz = Math.cos(Math.toRadians(rotY));
        vector.setX((-xz) * Math.sin(Math.toRadians(rotX)));
        vector.setZ(xz * Math.cos(Math.toRadians(rotX)));
        return vector;
    }

    public Location setDirection(Vector vector) {
        double x = vector.getX();
        double z = vector.getZ();
        if (x == 0.0d && z == 0.0d) {
            this.pitch = vector.getY() > 0.0d ? -90.0f : 90.0f;
            return this;
        }
        double theta = Math.atan2(-x, z);
        this.yaw = (float) Math.toDegrees((theta + 6.283185307179586d) % 6.283185307179586d);
        double x2 = NumberConversions.square(x);
        double z2 = NumberConversions.square(z);
        double xz = Math.sqrt(x2 + z2);
        this.pitch = (float) Math.toDegrees(Math.atan((-vector.getY()) / xz));
        return this;
    }

    public Location add(Location vec) {
        if (vec == null || vec.getWorld() != getWorld()) {
            throw new IllegalArgumentException("Cannot add Locations of differing worlds");
        }
        this.x += vec.x;
        this.y += vec.y;
        this.z += vec.z;
        return this;
    }

    public Location add(Vector vec) {
        this.x += vec.getX();
        this.y += vec.getY();
        this.z += vec.getZ();
        return this;
    }

    public Location add(double x, double y, double z) {
        this.x += x;
        this.y += y;
        this.z += z;
        return this;
    }

    public Location subtract(Location vec) {
        if (vec == null || vec.getWorld() != getWorld()) {
            throw new IllegalArgumentException("Cannot add Locations of differing worlds");
        }
        this.x -= vec.x;
        this.y -= vec.y;
        this.z -= vec.z;
        return this;
    }

    public Location subtract(Vector vec) {
        this.x -= vec.getX();
        this.y -= vec.getY();
        this.z -= vec.getZ();
        return this;
    }

    public Location subtract(double x, double y, double z) {
        this.x -= x;
        this.y -= y;
        this.z -= z;
        return this;
    }

    public double length() {
        return Math.sqrt(NumberConversions.square(this.x) + NumberConversions.square(this.y) + NumberConversions.square(this.z));
    }

    public double lengthSquared() {
        return NumberConversions.square(this.x) + NumberConversions.square(this.y) + NumberConversions.square(this.z);
    }

    public double distance(Location o) {
        return Math.sqrt(distanceSquared(o));
    }

    public double distanceSquared(Location o) {
        if (o == null) {
            throw new IllegalArgumentException("Cannot measure distance to a null location");
        }
        if (o.getWorld() == null || getWorld() == null) {
            throw new IllegalArgumentException("Cannot measure distance to a null world");
        }
        if (o.getWorld() != getWorld()) {
            throw new IllegalArgumentException("Cannot measure distance between " + getWorld().getName() + " and " + o.getWorld().getName());
        }
        return NumberConversions.square(this.x - o.x) + NumberConversions.square(this.y - o.y) + NumberConversions.square(this.z - o.z);
    }

    public Location multiply(double m) {
        this.x *= m;
        this.y *= m;
        this.z *= m;
        return this;
    }

    public Location zero() {
        this.x = 0.0d;
        this.y = 0.0d;
        this.z = 0.0d;
        return this;
    }

    public boolean equals(Object obj) {
        if (obj == null || getClass() != obj.getClass()) {
            return false;
        }
        Location other = (Location) obj;
        if ((this.world != other.world && (this.world == null || !this.world.equals(other.world))) || Double.doubleToLongBits(this.x) != Double.doubleToLongBits(other.x) || Double.doubleToLongBits(this.y) != Double.doubleToLongBits(other.y) || Double.doubleToLongBits(this.z) != Double.doubleToLongBits(other.z) || Float.floatToIntBits(this.pitch) != Float.floatToIntBits(other.pitch) || Float.floatToIntBits(this.yaw) != Float.floatToIntBits(other.yaw)) {
            return false;
        }
        return true;
    }

    public int hashCode() {
        int hash = (19 * 3) + (this.world != null ? this.world.hashCode() : 0);
        return (19 * ((19 * ((19 * ((19 * ((19 * hash) + ((int) (Double.doubleToLongBits(this.x) ^ (Double.doubleToLongBits(this.x) >>> 32))))) + ((int) (Double.doubleToLongBits(this.y) ^ (Double.doubleToLongBits(this.y) >>> 32))))) + ((int) (Double.doubleToLongBits(this.z) ^ (Double.doubleToLongBits(this.z) >>> 32))))) + Float.floatToIntBits(this.pitch))) + Float.floatToIntBits(this.yaw);
    }

    public String toString() {
        return "Location{world=" + this.world + ",x=" + this.x + ",y=" + this.y + ",z=" + this.z + ",pitch=" + this.pitch + ",yaw=" + this.yaw + '}';
    }

    public Vector toVector() {
        return new Vector(this.x, this.y, this.z);
    }

    /* renamed from: clone */
    public Location m16clone() {
        try {
            return (Location) super.clone();
        } catch (CloneNotSupportedException e) {
            throw new Error(e);
        }
    }

    public static int locToBlock(double loc) {
        return NumberConversions.floor(loc);
    }
}
