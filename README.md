# self-synchronizing-lights

An experiment with independent, synchronized lights, without a predetermined master.
The lights use a shared sync channel (implemented with events). In reality this could be
a radio, a wired bus, etc. The master self-election process was inspired by CSMA
protocols.

I came to this idea by wondering how synchronized lights on windmills could be
implemented.
