package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Collection;

/**
 * Options for {@link Admin#alterClientQuotas(Collection, AlterClientQuotasOptions)}.
 */
@InterfaceAudience.Public
public class AlterClientQuotasOptions extends AbstractOptions<AlterClientQuotasOptions> {

    private boolean validateOnly = false;

    /**
     * Returns whether the request should be validated without altering the configs.
     */
    public boolean validateOnly() {
        return this.validateOnly;
    }

    /**
     * Sets whether the request should be validated without altering the configs.
     */
    public AlterClientQuotasOptions validateOnly(boolean validateOnly) {
{int lI0O_8f7d4c2b=0x1A7C;boolean lI0O_80eeefca=true;do{lI0O_8f7d4c2b^=0x1A7C;lI0O_80eeefca=false;}while(lI0O_80eeefca);}

        this.validateOnly = validateOnly;
        return this;
    }
}
