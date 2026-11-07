package javax.microedition.shell.gothic;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.os.SystemClock;
import android.util.AttributeSet;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

import java.util.Arrays;

/**
 * Native Gothic 3 touch controls, completely separate from J2ME Loader's keyboard.
 * A dedicated, non-overlapping lower panel supports two-handed multitouch.
 */
public final class GothicControlsView extends View {
    public interface KeyListener {
        void onPressed(int code);
        void onRepeated(int code);
        void onReleased(int code);
    }

    private static final int ACTION = 0;
    private static final int TARGET = 1;
    private static final int SLOTS = 2;
    private static final int MENU = 3;
    private static final int BACK = 4;
    private static final int PAUSE = 5;
    private static final int BUTTON_COUNT = 6;
    // Standard MIDP key codes, not Android KeyEvent codes.
    private static final int[] KEY_CODES = {'5', '*', '#', -6, -7, '0'};
    private static final String[] LABELS = {"ДЕЙСТВИЕ", "ЦЕЛЬ", "СЛОТЫ", "МЕНЮ", "НАЗАД", "ПАУЗА"};

    private static final int DARK = Color.rgb(23, 19, 18);
    private static final int IRON = Color.rgb(57, 45, 37);
    private static final int BRONZE = Color.rgb(161, 123, 76);
    private static final int AMBER = Color.rgb(242, 191, 109);
    private static final int IVORY = Color.rgb(237, 219, 188);

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bounds = new RectF();
    private final float[] buttonX = new float[BUTTON_COUNT];
    private final float[] buttonY = new float[BUTTON_COUNT];
    private final float[] buttonRadius = new float[BUTTON_COUNT];
    private final float[] buttonAnimation = new float[BUTTON_COUNT];
    private final int[] buttonPointers = new int[BUTTON_COUNT];

    private KeyListener listener;
    private int joystickPointer = -1;
    private int directionKey;
    private float joystickX;
    private float joystickY;
    private float joystickRadius;
    private float knobX;
    private float knobY;
    private float knobTargetX;
    private float knobTargetY;
    private boolean controlsActive = true;
    private boolean hapticsEnabled = true;
    private boolean repeatScheduled;
    private long lastDirectionHaptic;

    private final Runnable repeatHeldKeys = new Runnable() {
        @Override
        public void run() {
            repeatScheduled = false;
            if (!controlsActive || !hasHeldKeys()) {
                return;
            }
            if (listener != null) {
                if (directionKey != 0) {
                    listener.onRepeated(directionKey);
                }
                for (int i = 0; i < BUTTON_COUNT; ++i) {
                    if (buttonPointers[i] != -1) {
                        listener.onRepeated(KEY_CODES[i]);
                    }
                }
            }
            repeatScheduled = true;
            postDelayed(this, 110);
        }
    };

    public GothicControlsView(Context context) {
        this(context, null);
    }

    public GothicControlsView(Context context, AttributeSet attrs) {
        super(context, attrs);
        Arrays.fill(buttonPointers, -1);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null); // soft shadows and gradients
        setFocusable(false);
        setClickable(true);
        setContentDescription("Gothic 3: игровой джойстик и кнопки");
        line.setStyle(Paint.Style.STROKE);
        line.setStrokeCap(Paint.Cap.ROUND);
        line.setStrokeJoin(Paint.Join.ROUND);
    }

    public static int recommendedHeight(Context context) {
        float density = context.getResources().getDisplayMetrics().density;
        float widthDp = context.getResources().getDisplayMetrics().widthPixels / density;
        float dp = Math.max(176f, Math.min(220f, widthDp * 0.55f));
        return Math.round(dp * density);
    }

    public void setKeyListener(KeyListener listener) {
        this.listener = listener;
    }

    public void setHapticsEnabled(boolean enabled) {
        hapticsEnabled = enabled;
    }

    public void setControlsActive(boolean active) {
        if (!active) {
            cancelInputs();
        }
        controlsActive = active;
        setAlpha(active ? 1f : 0.65f);
        invalidate();
    }

    private float dp(float value) {
        return value * getResources().getDisplayMetrics().density;
    }

    private void calculateGeometry() {
        float w = getWidth();
        float h = getHeight();
        joystickX = w * 0.24f;
        joystickY = h * 0.56f;
        joystickRadius = Math.min(w * 0.215f, h * 0.425f);
        buttonX[ACTION] = w * 0.826f;
        buttonY[ACTION] = h * 0.52f;
        buttonRadius[ACTION] = Math.min(w * 0.133f, h * 0.255f);
        buttonX[TARGET] = w * 0.56f;
        buttonY[TARGET] = h * 0.62f;
        buttonRadius[TARGET] = Math.min(w * 0.072f, h * 0.15f);
        buttonX[SLOTS] = w * 0.64f;
        buttonY[SLOTS] = h * 0.86f;
        buttonRadius[SLOTS] = Math.min(w * 0.069f, h * 0.138f);
        // Familiar navigation order, left to right: Menu | Pause | Back.
        // Assign actual button identities to these positions so touch targets,
        // captions and MIDP key mappings always move together.
        final int[] topRow = {MENU, PAUSE, BACK};
        for (int slot = 0; slot < topRow.length; slot++) {
            int index = topRow[slot];
            buttonX[index] = w * (0.55f + slot * 0.17f);
            buttonY[index] = h * 0.15f;
            buttonRadius[index] = Math.min(w * 0.073f, h * 0.12f);
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        calculateGeometry();
        float w = getWidth();
        float h = getHeight();

        paint.setStyle(Paint.Style.FILL);
        paint.setShader(new LinearGradient(0, 0, 0, h,
                new int[] {0xFF171311, 0xFF342923, 0xFF181412},
                null, Shader.TileMode.CLAMP));
        canvas.drawRect(0, 0, w, h, paint);
        paint.setShader(null);

        line.setColor(0xFF9D7852);
        line.setStrokeWidth(dp(1.3f));
        canvas.drawLine(0, dp(1.5f), w, dp(1.5f), line);
        line.setStrokeWidth(dp(0.6f));
        line.setColor(0x554C392A);
        canvas.drawLine(0, dp(4), w, dp(4), line);
        canvas.drawLine(dp(8), h - dp(6), w - dp(8), h - dp(6), line);

        drawJoystick(canvas);
        for (int i = 0; i < BUTTON_COUNT; ++i) {
            drawButton(canvas, i);
        }

        boolean animate = false;
        float nextX = knobX + (knobTargetX - knobX) * (joystickPointer == -1 ? 0.24f : 0.43f);
        float nextY = knobY + (knobTargetY - knobY) * (joystickPointer == -1 ? 0.24f : 0.43f);
        animate |= Math.abs(nextX - knobX) > 0.15f || Math.abs(nextY - knobY) > 0.15f;
        knobX = nextX;
        knobY = nextY;
        for (int i = 0; i < BUTTON_COUNT; ++i) {
            float desired = buttonPointers[i] == -1 ? 0f : 1f;
            float next = buttonAnimation[i] + (desired - buttonAnimation[i]) * 0.31f;
            animate |= Math.abs(next - buttonAnimation[i]) > 0.005f;
            buttonAnimation[i] = next;
        }
        if (animate) {
            postInvalidateOnAnimation();
        }
    }

    private void drawJoystick(Canvas canvas) {
        float x = joystickX;
        float y = joystickY;
        float r = joystickRadius;

        paint.setStyle(Paint.Style.FILL);
        paint.setShadowLayer(dp(6), 0, dp(3), 0xAA000000);
        paint.setColor(DARK);
        canvas.drawCircle(x, y, r + dp(1), paint);
        paint.clearShadowLayer();

        paint.setShader(new RadialGradient(x, y, r,
                new int[] {0xFF473C34, 0xFF27211E, 0xFF151311},
                null, Shader.TileMode.CLAMP));
        canvas.drawCircle(x, y, r, paint);
        paint.setShader(null);

        line.setStrokeWidth(dp(3));
        line.setColor(0xFF765B3D);
        canvas.drawCircle(x, y, r - dp(2), line);
        line.setStrokeWidth(dp(1));
        line.setColor(0xFFB89A71);
        canvas.drawCircle(x, y, r - dp(7), line);
        line.setColor(0x664F3C29);
        canvas.drawCircle(x, y, r * .66f, line);

        if (directionKey != 0) {
            float angle = directionAngle(directionKey);
            bounds.set(x - r * .88f, y - r * .88f, x + r * .88f, y + r * .88f);
            paint.setColor(0x55FFD096);
            paint.setStyle(Paint.Style.FILL);
            boolean diagonal = directionKey == '1' || directionKey == '3'
                    || directionKey == '7' || directionKey == '9';
            // Diagonals illuminate both adjacent cardinal sectors.
            float start = diagonal ? angle - 45f : angle - 23f;
            float sweep = diagonal ? 90f : 46f;
            canvas.drawArc(bounds, start, sweep, true, paint);
            line.setColor(AMBER);
            line.setStrokeWidth(dp(3.4f));
            if (diagonal) {
                canvas.drawArc(bounds, angle - 43f, 40f, false, line);
                canvas.drawArc(bounds, angle + 3f, 40f, false, line);
            } else {
                canvas.drawArc(bounds, angle - 21f, 42f, false, line);
            }
        }

        line.setColor(directionKey == 0 ? 0xFF907553 : AMBER);
        line.setStrokeWidth(dp(2.5f));
        float chevronR = r * .78f;
        for (int i = 0; i < 8; ++i) {
            float angle = (float) (i * Math.PI / 4);
            float px = x + (float) Math.cos(angle) * chevronR;
            float py = y + (float) Math.sin(angle) * chevronR;
            float activeAngle = directionAngle(directionKey);
            boolean adjacent = directionKey == '1' || directionKey == '3'
                    || directionKey == '7' || directionKey == '9';
            boolean activeDot = directionKey != 0
                    && (activeAngle == i * 45f
                        || (adjacent && Math.abs((i * 45f - activeAngle + 360f) % 360f - 45f) < .01f)
                        || (adjacent && Math.abs((activeAngle - i * 45f + 360f) % 360f - 45f) < .01f));
            line.setColor(activeDot ? AMBER : 0xFF876C4F);
            canvas.drawCircle(px, py, dp(1.8f), paintColor(line.getColor()));
        }

        float kx = x + knobX;
        float ky = y + knobY;
        float kr = r * .36f * (joystickPointer == -1 ? 1f : 0.95f);
        paint.setColor(0xFF070605);
        paint.setShadowLayer(dp(6), 0, dp(3), 0xBB000000);
        canvas.drawCircle(kx, ky, kr + dp(2), paint);
        paint.clearShadowLayer();
        paint.setShader(new LinearGradient(kx, ky - kr, kx, ky + kr,
                0xFF89725A, 0xFF34291F, Shader.TileMode.CLAMP));
        canvas.drawCircle(kx, ky, kr, paint);
        paint.setShader(null);
        line.setColor(directionKey == 0 ? 0xFFB79B77 : AMBER);
        line.setStrokeWidth(dp(1.5f));
        canvas.drawCircle(kx, ky, kr - dp(2), line);
        drawDiamond(canvas, kx, ky, kr * .29f, 0xFFDDC09A);
    }

    private Paint paintColor(int color) {
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(color);
        return paint;
    }

    private static float directionAngle(int key) {
        switch (key) {
            case '6': return 0f;
            case '9': return 45f;
            case '8': return 90f;
            case '7': return 135f;
            case '4': return 180f;
            case '1': return 225f;
            case '2': return 270f;
            case '3': return 315f;
            default: return 0f;
        }
    }

    private void drawButton(Canvas canvas, int index) {
        float x = buttonX[index];
        float y = buttonY[index];
        float r = buttonRadius[index];
        float pressed = buttonAnimation[index];
        boolean small = index >= MENU;
        if (small) {
            float halfWidth = r * 1.18f;
            float halfHeight = r * .46f;
            bounds.set(x - halfWidth, y - halfHeight, x + halfWidth, y + halfHeight);
            paint.setColor(0xFF110D0B);
            paint.setShadowLayer(dp(3), 0, dp(2), 0xBB000000);
            canvas.drawRoundRect(bounds, dp(6), dp(6), paint);
            paint.clearShadowLayer();
            paint.setShader(new LinearGradient(0, bounds.top, 0, bounds.bottom,
                    pressed > .02f ? 0xFF9A633B : 0xFF554439,
                    pressed > .02f ? 0xFF5B3923 : 0xFF2A231F,
                    Shader.TileMode.CLAMP));
            canvas.drawRoundRect(bounds, dp(6), dp(6), paint);
            paint.setShader(null);
            line.setColor(pressed > .05f ? AMBER : BRONZE);
            line.setStrokeWidth(dp(1));
            canvas.drawRoundRect(bounds, dp(6), dp(6), line);
            drawText(canvas, LABELS[index], x, y + dp(3.6f), dp(9.2f),
                    pressed > .1f ? 0xFFFFE9BE : IVORY);
            return;
        }

        float scale = 1f - pressed * 0.065f;
        canvas.save();
        canvas.scale(scale, scale, x, y);
        paint.setColor(0xFF13100D);
        paint.setShadowLayer(dp(5), 0, dp(3), 0xBB000000);
        canvas.drawCircle(x, y, r + dp(1), paint);
        paint.clearShadowLayer();
        paint.setShader(new LinearGradient(x, y - r, x, y + r,
                pressed > .02f ? 0xFFB27F45 : 0xFF77604A,
                pressed > .02f ? 0xFF52351F : 0xFF2B251F,
                Shader.TileMode.CLAMP));
        canvas.drawCircle(x, y, r, paint);
        paint.setShader(null);
        line.setStrokeWidth(dp(index == ACTION ? 2.6f : 1.7f));
        line.setColor(pressed > .05f ? AMBER : BRONZE);
        canvas.drawCircle(x, y, r - dp(2), line);
        line.setStrokeWidth(dp(.7f));
        line.setColor(0x88E2C296);
        canvas.drawCircle(x, y, r * .85f, line);
        if (pressed > .02f) {
            paint.setShader(new RadialGradient(x, y, r,
                    new int[] {0x66FFCC80, 0x00FFCC80},
                    null, Shader.TileMode.CLAMP));
            canvas.drawCircle(x, y, r, paint);
            paint.setShader(null);
        }
        drawButtonIcon(canvas, index, x, y - r * .23f, r);
        drawText(canvas, LABELS[index], x, y + r * .53f,
                index == ACTION ? dp(9f) : dp(8.3f),
                pressed > .1f ? 0xFFFFFFFF : IVORY);
        canvas.restore();
    }

    private void drawButtonIcon(Canvas canvas, int index, float x, float y, float r) {
        line.setColor(IVORY);
        line.setStrokeWidth(dp(index == ACTION ? 3.0f : 2f));
        if (index == ACTION) {
            float d = r * .33f;
            canvas.drawLine(x - d, y - d, x + d, y + d, line);
            canvas.drawLine(x + d, y - d, x - d, y + d, line);
            canvas.drawLine(x - d - dp(3), y + d - dp(1), x - d + dp(5), y + d + dp(7), line);
            canvas.drawLine(x + d + dp(3), y + d - dp(1), x + d - dp(5), y + d + dp(7), line);
        } else if (index == TARGET) {
            float cr = r * .28f;
            canvas.drawCircle(x, y, cr, line);
            canvas.drawLine(x - cr * 1.65f, y, x - cr * .7f, y, line);
            canvas.drawLine(x + cr * .7f, y, x + cr * 1.65f, y, line);
            canvas.drawLine(x, y - cr * 1.65f, x, y - cr * .7f, line);
            canvas.drawLine(x, y + cr * .7f, x, y + cr * 1.65f, line);
        } else if (index == SLOTS) {
            drawDiamond(canvas, x - r * .28f, y, r * .21f, IVORY);
            drawDiamond(canvas, x + r * .08f, y - r * .16f, r * .21f, IVORY);
            drawDiamond(canvas, x + r * .26f, y + r * .19f, r * .18f, IVORY);
        }
    }

    private void drawDiamond(Canvas canvas, float x, float y, float r, int color) {
        Path diamond = new Path();
        diamond.moveTo(x, y - r);
        diamond.lineTo(x + r, y);
        diamond.lineTo(x, y + r);
        diamond.lineTo(x - r, y);
        diamond.close();
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(color);
        canvas.drawPath(diamond, paint);
    }

    private void drawText(Canvas canvas, String value, float x, float baseline,
                          float size, int color) {
        paint.setShader(null);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(color);
        paint.setTextSize(size);
        paint.setTypeface(android.graphics.Typeface.create("serif", android.graphics.Typeface.BOLD));
        paint.setTextAlign(Paint.Align.CENTER);
        canvas.drawText(value, x, baseline, paint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (!controlsActive) return true;
        calculateGeometry();
        int action = event.getActionMasked();
        int pointerIndex = event.getActionIndex();
        if (action == MotionEvent.ACTION_CANCEL) {
            cancelInputs();
            return true;
        }
        if (action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_POINTER_DOWN) {
            int id = event.getPointerId(pointerIndex);
            startPointer(id, event.getX(pointerIndex), event.getY(pointerIndex));
            invalidate();
            return true;
        }
        if (action == MotionEvent.ACTION_MOVE) {
            if (joystickPointer >= 0) {
                int index = event.findPointerIndex(joystickPointer);
                if (index >= 0) moveJoystick(event.getX(index), event.getY(index));
            }
            invalidate();
            return true;
        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_POINTER_UP) {
            int id = event.getPointerId(pointerIndex);
            releasePointer(id);
            invalidate();
            return true;
        }
        return true;
    }

    private void startPointer(int id, float x, float y) {
        float dx = x - joystickX;
        float dy = y - joystickY;
        if (joystickPointer == -1 && x < getWidth() * .46f
                && y > getHeight() * .24f
                && dx * dx + dy * dy <= (joystickRadius * 1.28f) * (joystickRadius * 1.28f)) {
            joystickPointer = id;
            moveJoystick(x, y);
            return;
        }
        int candidate = -1;
        float best = Float.MAX_VALUE;
        for (int i = 0; i < BUTTON_COUNT; ++i) {
            if (buttonPointers[i] != -1) continue;
            float distanceX = x - buttonX[i];
            float distanceY = y - buttonY[i];
            float radius = i >= MENU ? Math.max(dp(23), buttonRadius[i] * 1.2f)
                    : buttonRadius[i] + dp(7);
            float normalized;
            if (i >= MENU) {
                normalized = (distanceX * distanceX) / (radius * radius * 1.3f) +
                        (distanceY * distanceY) / ((radius * .96f) * (radius * .96f));
            } else {
                normalized = (distanceX * distanceX + distanceY * distanceY) / (radius * radius);
            }
            if (normalized <= 1f && normalized < best) {
                best = normalized;
                candidate = i;
            }
        }
        if (candidate >= 0) {
            buttonPointers[candidate] = id;
            if (listener != null) listener.onPressed(KEY_CODES[candidate]);
            haptic(HapticFeedbackConstants.VIRTUAL_KEY);
            startRepeatingIfNecessary();
        }
    }

    private void moveJoystick(float x, float y) {
        float dx = x - joystickX;
        float dy = y - joystickY;
        float r = joystickRadius * .46f;
        float len = (float) Math.hypot(dx, dy);
        if (len > r) {
            dx *= r / len;
            dy *= r / len;
        }
        knobTargetX = dx;
        knobTargetY = dy;
        int newDirection = GothicDirections.keyFor(
                x - joystickX, y - joystickY, joystickRadius * .22f);
        if (newDirection != directionKey) {
            if (listener != null) {
                if (directionKey != 0) listener.onReleased(directionKey);
                if (newDirection != 0) listener.onPressed(newDirection);
            }
            long now = SystemClock.uptimeMillis();
            if (newDirection != 0 && now - lastDirectionHaptic > 90) {
                haptic(HapticFeedbackConstants.CLOCK_TICK);
                lastDirectionHaptic = now;
            }
            directionKey = newDirection;
            startRepeatingIfNecessary();
        }
    }

    private void releasePointer(int id) {
        if (joystickPointer == id) {
            joystickPointer = -1;
            knobTargetX = 0;
            knobTargetY = 0;
            if (directionKey != 0 && listener != null) listener.onReleased(directionKey);
            directionKey = 0;
        }
        for (int i = 0; i < BUTTON_COUNT; ++i) {
            if (buttonPointers[i] == id) {
                buttonPointers[i] = -1;
                if (listener != null) listener.onReleased(KEY_CODES[i]);
            }
        }
        if (!hasHeldKeys()) {
            stopRepeating();
        }
    }

    private void haptic(int type) {
        if (hapticsEnabled && isHapticFeedbackEnabled()) {
            performHapticFeedback(type);
        }
    }

    private boolean hasHeldKeys() {
        if (directionKey != 0) return true;
        for (int id : buttonPointers) {
            if (id != -1) return true;
        }
        return false;
    }

    private void startRepeatingIfNecessary() {
        if (!repeatScheduled && hasHeldKeys()) {
            repeatScheduled = true;
            postDelayed(repeatHeldKeys, 350);
        }
    }

    private void stopRepeating() {
        removeCallbacks(repeatHeldKeys);
        repeatScheduled = false;
    }

    /** Release keys even if Android interrupts the gesture / pauses the Activity. */
    public void cancelInputs() {
        stopRepeating();
        if (directionKey != 0 && listener != null) listener.onReleased(directionKey);
        directionKey = 0;
        joystickPointer = -1;
        knobTargetX = 0f;
        knobTargetY = 0f;
        for (int i = 0; i < BUTTON_COUNT; ++i) {
            if (buttonPointers[i] != -1 && listener != null) {
                listener.onReleased(KEY_CODES[i]);
            }
            buttonPointers[i] = -1;
        }
        invalidate();
    }

    @Override
    protected void onDetachedFromWindow() {
        cancelInputs();
        super.onDetachedFromWindow();
    }
}
