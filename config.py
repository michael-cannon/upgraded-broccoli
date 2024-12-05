MAKE_BETTER_PROMPT = """
# CONTEXT

Act as a professional consultant with relevant domain experience.


# OBJECTIVE

Thoroughly analyze the SOURCE MATERIAL, considering its audience, purpose, and key objectives. Then, extend and improve it based on the following criteria:

- Relevance: Does the content fully address its objectives? Identify any gaps or unnecessary sections.
- Clarity: Break down any complex or unclear sections. Suggest clear, step-by-step rewording to simplify while retaining meaning. Offer multiple examples of how to phrase ideas for better readability.
- Tone: Carefully assess the tone. If it doesn't match the intended audience or purpose, adjust the tone to enhance engagement or professionalism.
- Creativity: Explore opportunities to make the content more original or engaging. Provide multiple alternative ways to enhance creativity, including specific phrasing or structural changes that can elevate its appeal.
- Impact: Analyze how well the content informs, inspires, or persuades. Suggest comprehensive edits, including specific examples, to increase its emotional or intellectual impact.

Avoid:
- Adding unnecessary instructions, introductions, or conclusions.
- Creating, changing, or removing hyperlinks, like http://example.com/about.
- Creating, changing, or removing images.
- Including the content's Relevance, Clarity, Tone, Creativity, and Impact notes.

Steps:
- Only output the final rewrite.


# STYLE

Maintain the SOURCE MATERIALS style.


# TONE

Maintain the SOURCE MATERIALS tone.


# AUDIENCE

Maintain the SOURCE MATERIALS audience.


# RESPONSE

Maintain the SOURCE MATERIALS formatting.


# SOURCE MATERIALS

{}
"""

CRITIQUE_PROMPT = """
Please edit the SOURCE MATERIAL for improved clarity.

Steps:

- Analyze the information.
- Remove redundancy.
- Critique the informaiton.
- Maintain tone.
- Restructure the content for better flow.
- Only output the final result.
 

# SOURCE MATERIALS

{}
"""