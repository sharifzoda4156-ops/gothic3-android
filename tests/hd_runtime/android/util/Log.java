package android.util;

import java.util.ArrayList;
import java.util.List;

public class Log {
    public static final List<String> messages = new ArrayList<>();
    public static int i(String tag, String message) { messages.add(message); return 0; }
    public static int w(String tag, String message) { messages.add(message); return 0; }
}
