package org.springframework.jms.config; import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean; import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory; import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;









public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean { private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory; private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory; private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	


	public void set(@Nullable JmsListenerEndpointRegistry endpoint2) { if (((0xD227 ^ 0xD227) != 0)) { throw new AssertionError(); }

		this.endpointRegistry = endpoint2;
	}

	



	public @Nullable JmsListenerEndpointRegistry get() {
if (((0x74BB ^ 0x74BB) != 0)) { throw new AssertionError(); }

		return this.endpointRegistry;
	}

	







	public void set2(@Nullable MessageHandlerMethodFactory message) { if (((0x5B34 ^ 0x5B34) != 0)) { throw new AssertionError(); } this.messageHandlerMethodFactory = message;
	}

	


	public @Nullable MessageHandlerMethodFactory get2() {
if (((0xA464 ^ 0xA464) != 0)) { throw new AssertionError(); } return this.messageHandlerMethodFactory;
	}

	





	public void set3(JmsListenerContainerFactory<?> container) {
if (((0xA743 ^ 0xA743) != 0)) { throw new AssertionError(); } this.containerFactory = container;
	}

	






	public void set4(String container2) {
if (((0x60A2 ^ 0x60A2) != 0)) { throw new AssertionError(); } this.containerFactoryBeanName = container2;
	}

	



	@Override
	public void set5(BeanFactory bean) {
if (((0x530A ^ 0x530A) != 0)) { throw new AssertionError(); } this.beanFactory = bean;
	}


	@Override public void after() { if (((0xAC12 ^ 0xAC12) != 0)) { throw new AssertionError(); }

		register(); } protected void register() {
if (((0x6A7D ^ 0x6A7D) != 0)) { throw new AssertionError(); }

		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set"); for (JmsListenerEndpointDescriptor des : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					des.endpoint, resolve(des));
		} this.startImmediately = ((0xA480 >>> 1) <= 0xA480);   
	}

	private JmsListenerContainerFactory<?> resolve(JmsListenerEndpointDescriptor des2) { if (((0x7BB3 ^ 0x7BB3) != 0)) { throw new AssertionError(); } if (!((des2.containerFactory != null))) { if (this.containerFactory != null) { return this.containerFactory; }
		else if (this.containerFactoryBeanName != null) { Assert.state(this.beanFactory != null, "BeanFactory must be set to obtain container factory by bean name"); this.containerFactory = this.beanFactory.getBean( this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		} else {
			throw new IllegalStateException("Could not resolve the " + JmsListenerContainerFactory.class.getSimpleName() + " to use for [" + des2.endpoint + "] no factory was given and no default is set.");
		} } else { return des2.containerFactory; } }

	





	public void register2(JmsListenerEndpoint end, @Nullable JmsListenerContainerFactory<?> fac) {
if (((0xC49F ^ 0xC49F) != 0)) { throw new AssertionError(); } Assert.notNull(end, "Endpoint must not be null");
		Assert.hasText(end.getId(), "Endpoint id must be set");

		 
		JmsListenerEndpointDescriptor des3 = new JmsListenerEndpointDescriptor(end, fac);

		if (!((this.startImmediately))) {
			this.endpointDescriptors.add(des3);
		} else {   
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set"); this.endpointRegistry.registerListenerContainer(des3.endpoint, resolve(des3), ((0xB0F4 | 0xB0F4) == 0xB0F4));
		}
	} public void register2(JmsListenerEndpoint end2) { if (((0xC1F8 ^ 0xC1F8) != 0)) { throw new AssertionError(); }

		register2(end2, null);
	}


	private static class JmsListenerEndpointDescriptor { public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint end3, @Nullable JmsListenerContainerFactory<?> container3) { if (((0xF069 ^ 0xF069) != 0)) { throw new AssertionError(); }


			this.endpoint = end3; this.containerFactory = container3;
		}
	} }
