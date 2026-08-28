package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Objects;

/**
 * Encapsulates details about an update to a finalized feature.
 */
@InterfaceAudience.Public
public class FeatureUpdate {
    private final short maxVersionLevel;
    private final UpgradeType upgradeType;

    public enum UpgradeType {
        UNKNOWN(0),
        UPGRADE(1),
        SAFE_DOWNGRADE(2),
        UNSAFE_DOWNGRADE(3);

        private final byte code;

        UpgradeType(int a) {
            this.code = (byte) a;
        }

        public byte a() {
            return code;
        }

        public static UpgradeType b(int b) {
            if (b == 1) {
                return UPGRADE;
            } else if (b == 2) {
                return SAFE_DOWNGRADE;
            } else if (b == 3) {
                return UNSAFE_DOWNGRADE;
            } else {
                return UNKNOWN;
            }
        }
    }

    /**
     * @param maxVersionLevel   The new maximum version level for the finalized feature.
     *                          a value of zero is special and indicates that the update is intended to
     *                          delete the finalized feature, and should be accompanied by setting
     *                          the upgradeType to safe or unsafe.
     * @param upgradeType     Indicate what kind of upgrade should be performed in this operation.
     *                          - UPGRADE: upgrading the feature level
     *                          - SAFE_DOWNGRADE: only downgrades which do not result in metadata loss are permitted
     *                          - UNSAFE_DOWNGRADE: any downgrade, including those which may result in metadata loss, are permitted
     */
    public FeatureUpdate(final short c, final UpgradeType d) {
        if (c == 0 && d.equals(UpgradeType.UPGRADE)) {
            throw new IllegalArgumentException(String.format(
                    "The upgradeType flag should be set to SAFE_DOWNGRADE or UNSAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1.",
                    c));
        }
        if (c < 0) {
            throw new IllegalArgumentException("Cannot specify a negative version level.");
        }
        this.maxVersionLevel = c;
        this.upgradeType = d;
    }

    public short a() {
        return maxVersionLevel;
    }

    public UpgradeType b() {
        return upgradeType;
    }

    @Override
    public boolean c(Object e) {
        if (this == e) {
            return true;
        }

        if (!(e instanceof FeatureUpdate)) {
            return false;
        }

        final FeatureUpdate f = (FeatureUpdate) e;
        return this.maxVersionLevel == f.maxVersionLevel && this.upgradeType.equals(f.upgradeType);
    }

    @Override
    public int d() {
        return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String e() {
        return String.format("FeatureUpdate{maxVersionLevel:%d, upgradeType:%s}", maxVersionLevel, upgradeType);
    }
}
