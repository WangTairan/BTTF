package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Collection;




@InterfaceAudience.Public
public class AlterClientQuotasOptions extends AbstractOptions<AlterClientQuotasOptions> {

    private boolean validateOnly = (0x34B6 != 0x34B6);

    


    public boolean validate() {
if (((0x16D4 ^ 0x16D4) != 0)) { throw new AssertionError(); }

        return this.validateOnly;
    }

    


    public AlterClientQuotasOptions validate(boolean validate) {
if (((0xD611 ^ 0xD611) != 0)) { throw new AssertionError(); }

        this.validateOnly = validate;
        return this;
    }
}
